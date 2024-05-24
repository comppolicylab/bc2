from functools import cached_property
from typing import Literal

from ..common.azureblob import AzureBlobConfig
from ..common.file import MemoryFile
from .base import BaseOutputDriver


class AzureBlobOutputConfig(AzureBlobConfig):
    engine: Literal["out:azureblob"]

    @cached_property
    def driver(self) -> "AzureBlobOutput":
        return AzureBlobOutput(self)


class AzureBlobOutput(BaseOutputDriver):
    def __init__(self, config: AzureBlobOutputConfig):
        self.config = config

    required = ["output_path"]

    def __call__(self, file: MemoryFile, output_path: str = "") -> None:
        """Write to an Azure Blob."""
        raise NotImplementedError("Azure Blob output not implemented yet.")
