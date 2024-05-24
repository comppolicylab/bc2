from functools import cached_property

from ..common.azureblob import AzureBlobConfig
from ..common.file import MemoryFile
from .base import BaseInputDriver


class AzureBlobInputConfig(AzureBlobConfig):
    @cached_property
    def driver(self) -> "AzureBlobInput":
        return AzureBlobInput(self)


class AzureBlobInput(BaseInputDriver):
    def __init__(self, config: AzureBlobInputConfig):
        self.config = config

    required = ["input_path"]

    def __call__(self, input_path: str = "") -> MemoryFile:
        """Read from an Azure Blob."""
        raise NotImplementedError("Azure Blob input not implemented yet.")
