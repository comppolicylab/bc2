from ..common.azureblob import AzureBlobConfig
from ..common.file import MemoryFile
from .base import BaseInputDriver


class AzureBlobInputConfig(AzureBlobConfig):
    pass


class AzureBlobInput(BaseInputDriver):
    def __init__(self, config: AzureBlobInputConfig):
        self.config = config

    def __call__(self, path: str = "") -> MemoryFile:
        """Read from an Azure Blob."""
        raise NotImplementedError("Azure Blob input not implemented yet.")
