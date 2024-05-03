import os
import shutil
from abc import abstractmethod
from typing import Generator, List, Protocol

from azure.core.credentials import AzureNamedKeyCredential
from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


class FileIO(Protocol):
    """Read/write files from somewhere."""

    @abstractmethod
    def read_binary(self, name: str) -> bytes: ...

    @abstractmethod
    def read(self, name: str) -> str: ...

    @abstractmethod
    def write(self, name: str, contents: str, overwrite: bool = False) -> None: ...

    @abstractmethod
    def list(self, path: str) -> Generator[str, None, None]: ...

    @abstractmethod
    def copy(self, name: str, dest: str) -> None: ...

    @abstractmethod
    def join(self, *paths: str) -> str: ...

    @abstractmethod
    def basename(self, name: str) -> str: ...

    @abstractmethod
    def exists(self, name: str) -> bool: ...

    @abstractmethod
    def splitpath(self, name: str) -> List[str]: ...

    @abstractmethod
    def delete(self, name: str) -> None: ...

    @abstractmethod
    def __hash__(self) -> int:
        """Client should be hashable for caching."""
        ...


class LocalFileIO(FileIO):
    """Read/write files from the local filesystem."""

    def __init__(self, root: str = "."):
        self._root = root

    def read_binary(self, name: str) -> bytes:
        fp = os.path.join(self._root, name)
        with open(fp, "rb") as f:
            return f.read()

    def read(self, name: str) -> str:
        fp = os.path.join(self._root, name)
        with open(fp) as f:
            return f.read()

    def write(self, name: str, contents: str, overwrite: bool = False) -> None:
        if not overwrite and self.exists(name):
            raise FileExistsError(f"File {name} already exists")
        fp = os.path.join(self._root, name)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w") as f:
            f.write(contents)

    def list(self, path: str) -> Generator[str, None, None]:
        for root, _, files in os.walk(os.path.join(self._root, path)):
            for name in files:
                yield os.path.relpath(os.path.join(root, name), self._root)

    def copy(self, name: str, dest: str) -> None:
        src = os.path.join(self._root, name)
        dst = os.path.join(self._root, dest)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)

    def join(self, *paths: str) -> str:
        return os.path.join(*paths)

    def basename(self, name: str) -> str:
        return os.path.basename(name)

    def exists(self, name: str) -> bool:
        return os.path.exists(os.path.join(self._root, name))

    def splitpath(self, name: str) -> List[str]:
        return name.split(os.path.sep)

    def delete(self, name: str) -> None:
        os.remove(os.path.join(self._root, name))

    def __hash__(self) -> int:
        return hash(self._root)


class AzureFileIO(FileIO):
    """Read/write files from Azure Blob Storage."""

    def __init__(self, account_url: str, container: str, key: str = ""):
        self._account_url = account_url
        self._container = container
        cred = DefaultAzureCredential()
        if key:
            # Parse key name from account URL
            # e.g. https://myaccount.blob.core.windows.net -> myaccount
            name = account_url.split(".")[0].split("//")[-1]
            cred = AzureNamedKeyCredential(name, key)
        self._blob_client = BlobServiceClient(account_url=account_url, credential=cred)
        self._container_client = self._blob_client.get_container_client(container)

    @property
    def container_url(self) -> str:
        """Get the URL of the container."""
        return self._container_client.url

    def read_binary(self, name: str) -> bytes:
        """Read a file from Azure Blob Storage as binary."""
        blob = self._container_client.download_blob(name)
        return blob.readall()

    def read(self, name: str) -> str:
        """Read a file from Azure Blob Storage."""
        blob = self._container_client.download_blob(name, encoding="utf-8")
        return blob.readall()

    def write(self, name: str, contents: str, overwrite: bool = False) -> None:
        """Write a file to Azure Blob Storage."""
        try:
            self._container_client.upload_blob(
                name, contents, encoding="utf-8", overwrite=overwrite
            )
        except ResourceExistsError:
            raise FileExistsError(f"File {name} already exists")

    def list(self, path: str) -> Generator[str, None, None]:
        """List files in a directory."""
        if not path.endswith("/"):
            path += "/"
        for name in self._container_client.list_blob_names(name_starts_with=path):
            yield name

    def copy(self, name: str, dest: str) -> None:
        """Copy a file within Azure Blob Storage."""
        new_blob = self._container_client.get_blob_client(dest)
        source_url = self._container_client.url + "/" + name
        new_blob.upload_blob_from_url(source_url)

    def join(self, *paths: str) -> str:
        """Join paths."""
        return "/".join(paths)

    def basename(self, name: str) -> str:
        """Get the basename of a file."""
        return name.split("/")[-1]

    def exists(self, name: str) -> bool:
        """Check if a file exists."""
        return self._container_client.get_blob_client(name).exists()

    def splitpath(self, name: str) -> List[str]:
        """Split a path into its parts."""
        return name.split("/")

    def delete(self, name: str) -> None:
        """Delete a file."""
        self._container_client.delete_blob(name, delete_snapshots="include")

    def __hash__(self) -> int:
        return hash((self._account_url, self._container))
