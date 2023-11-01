import os
from abc import abstractmethod
from typing import Protocol

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


class FileReader(Protocol):
    """Read files from somewhere."""

    @abstractmethod
    def read(self, name: str) -> str:
        raise NotImplementedError


class LocalFileReader(FileReader):
    """Read files from the local filesystem."""

    def __init__(self, root: str = "."):
        self._root = root

    def read(self, name: str) -> str:
        fp = os.path.join(self._root, name)
        with open(fp) as f:
            return f.read()


class AzureFileReader(FileReader):
    """Read files from Azure Blob Storage."""

    def __init__(self, account_url: str, container: str):
        self._account_url = account_url
        self._container = container
        self._client = BlobServiceClient(
            account_url=account_url, credential=DefaultAzureCredential()
        )

    def read(self, name: str) -> str:
        """Read a file from Azure Blob Storage."""
        container_client = self._client.get_container_client(self._container)
        blob = container_client.download_blob(name, encoding="utf-8")
        return blob.readall()
