from functools import cached_property
from typing import Literal

from ..common.azureblob import AzureBlobConfig, AzureBlobDriver
from ..common.file import MemoryFile
from .base import BaseOutputDriver


class AzureBlobOutputConfig(AzureBlobConfig):
    engine: Literal["out:azureblob"]

    @cached_property
    def driver(self) -> "AzureBlobOutput":
        return AzureBlobOutput(self)


class AzureBlobOutput(BaseOutputDriver, AzureBlobDriver):
    required = ["output_path"]

    def __init__(self, config: AzureBlobOutputConfig):
        self.init_client(config)

    def __call__(self, file: MemoryFile, output_path: str = "") -> None:
        """Write to an Azure Blob."""
        full_path = f"{self.config.prefix}{output_path}"
        bc = self.blob_service_client.get_blob_client(
            container=self.config.container, blob=full_path
        )
        bc.upload_blob(file.buffer, blob_type="BlockBlob")
