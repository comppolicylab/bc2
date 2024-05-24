from pydantic import BaseModel, Field


class AzureBlobConfig(BaseModel):
    """Azure Blob config."""

    connection_string: str
    container: str
    prefix: str = Field("")
