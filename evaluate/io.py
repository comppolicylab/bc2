import os
from abc import abstractmethod
from typing import Generator, Protocol

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


class FileReader(Protocol):
    """Read files from somewhere."""

    @abstractmethod
    def read(self, name: str) -> str:
        ...

    @abstractmethod
    def list(self, path: str) -> Generator[str, None, None]:
        ...


class LocalFileReader(FileReader):
    """Read files from the local filesystem."""

    def __init__(self, root: str = "."):
        self._root = root

    def read(self, name: str) -> str:
        fp = os.path.join(self._root, name)
        with open(fp) as f:
            return f.read()

    def list(self, path: str) -> Generator[str, None, None]:
        for root, _, files in os.walk(os.path.join(self._root, path)):
            for name in files:
                yield os.path.relpath(os.path.join(root, name), self._root)


class AzureFileReader(FileReader):
    """Read files from Azure Blob Storage."""

    def __init__(self, account_url: str, container: str):
        self._account_url = account_url
        self._container = container
        self._blob_client = BlobServiceClient(
            account_url=account_url, credential=DefaultAzureCredential()
        )
        self._container_client = self._blob_client.get_container_client(container)

    def read(self, name: str) -> str:
        """Read a file from Azure Blob Storage."""
        blob = self._container_client.download_blob(name, encoding="utf-8")
        return blob.readall()

    def list(self, path: str) -> Generator[str, None, None]:
        """List files in a directory."""
        for blob in self._container_client.list_blobs(path):
            yield blob.name
