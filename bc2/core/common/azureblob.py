from azure.core.credentials import AzureNamedKeyCredential
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from pydantic import BaseModel, Field


class AzureBlobConfig(BaseModel):
    """Azure Blob config."""

    account_url: str
    container: str
    api_key: str = Field("")
    prefix: str = Field("")


class AzureBlobDriver:
    def init_client(self, config: AzureBlobConfig):
        self.config = config
        cred = DefaultAzureCredential()
        if config.api_key:
            # Parse key name from account URL
            # e.g. https://myaccount.blob.core.windows.net -> myaccount
            name = config.account_url.split(".")[0].split("//")[-1]
            cred = AzureNamedKeyCredential(name, config.api_key)

        self.blob_service_client = BlobServiceClient(
            account_url=config.account_url, credential=cred
        )
        self.container_client = self.blob_service_client.get_container_client(
            config.container
        )
