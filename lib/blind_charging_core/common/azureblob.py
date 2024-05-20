from typing import Literal

from pydantic import BaseModel, Field


class AzureBlobConfig(BaseModel):
    """Azure Blob config."""

    engine: Literal["azureblob"]
    connection_string: str
    container: str
    prefix: str = Field("")
