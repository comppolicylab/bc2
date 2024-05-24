from functools import cached_property
from typing import Literal

from ..common.azureblob import AzureBlobConfig, AzureBlobDriver
from ..common.file import MemoryFile
from .base import BaseInputDriver


class AzureBlobInputConfig(AzureBlobConfig):
    engine: Literal["in:azureblob"]

    @cached_property
    def driver(self) -> "AzureBlobInput":
        return AzureBlobInput(self)


class AzureBlobInput(BaseInputDriver, AzureBlobDriver):
    required = ["input_path"]

    def __init__(self, config: AzureBlobInputConfig):
        self.init_client(config)

    def __call__(self, input_path: str = "") -> MemoryFile:
        """Read from an Azure Blob."""
        f = MemoryFile()
        full_path = f"{self.config.prefix}{input_path}"
        blob = self.container_client.download_blob(full_path)
        blob.readinto(f.buffer)
        return f
