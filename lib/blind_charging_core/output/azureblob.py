from ..common.azureblob import AzureBlobConfig
from ..common.file import MemoryFile
from .base import BaseOutputDriver


class AzureBlobOutputConfig(AzureBlobConfig):
    pass


class AzureBlobOutput(BaseOutputDriver):
    def __init__(self, config: AzureBlobOutputConfig):
        self.config = config

    def __call__(self, file: MemoryFile, path: str = "") -> None:
        """Write to an Azure Blob."""
        raise NotImplementedError("Azure Blob output not implemented yet.")
