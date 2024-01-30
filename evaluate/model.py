import logging
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from azure.ai.formrecognizer import (
    DocumentAnalysisClient,
    DocumentModelAdministrationClient,
    ModelBuildMode,
)
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

from .io import AzureFileIO
from .label import BoundingBox, Labels

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a model."""

    model_id: str
    description: str | None
    tags: dict[str, str] | None
    created_on: datetime
    expires_on: datetime | None
    api_version: str | None


class AzureModelClient:
    def __init__(self, endpoint: str, key: str = ""):
        """Initialize the client.

        Args:
            endpoint: endpoint URL
            key: API key
        """
        cred = DefaultAzureCredential() if not key else AzureKeyCredential(key)
        self.dmac = DocumentModelAdministrationClient(
            endpoint=endpoint, credential=cred
        )
        self.dac = DocumentAnalysisClient(endpoint=endpoint, credential=cred)

    def runner(self, store: AzureFileIO) -> "AzureModelRunner":
        """Get a model runner."""
        return AzureModelRunner(self.dac, store)

    def trainer(self, store: AzureFileIO) -> "AzureModelTrainer":
        """Get a model trainer."""
        return AzureModelTrainer(self.dmac, store)

    def list_models(self) -> list[ModelInfo]:
        """List models."""
        return [
            ModelInfo(
                model_id=m.model_id,
                description=m.description,
                tags=m.tags,
                created_on=m.created_on,
                expires_on=m.expires_on,
                api_version=m.api_version,
            )
            for m in self.dmac.list_document_models()
        ]


class ModelRunner(Protocol):
    """Run a model."""

    @abstractmethod
    def run(self, model_id: str, path: str) -> Labels:
        """Run a model on the documents at the given path.

        Args:
            model_id: ID of the model
            path: path to the documents

        Returns:
            Fields identified in the document
        """
        ...


class AzureModelRunner(ModelRunner):
    def __init__(self, cli: DocumentAnalysisClient, store: AzureFileIO):
        """Initialize the runner."""
        self.cli = cli
        self.store = store

    def run(self, model_id: str, path: str) -> Labels:
        """Run a model on the documents at the given path.

        Args:
            model_id: ID of the model
            path: path to the documents

        Returns:
            Fields identified in the document
        """
        logger.info(
            f"Running model {model_id} on documents in "
            f"{self.store.container_url} at {path}"
        )

        url = self.store.join(self.store.container_url, path)

        poller = self.cli.begin_analyze_document_from_url(
            model_id=model_id,
            document_url=url,
        )

        logger.info("Waiting for model run to complete...")
        result = poller.result()
        logger.info("Model run complete.")
        if len(result.documents) != 1:
            raise ValueError("Expected exactly one document in result")
        labels = Labels()
        for key, field in result.documents[0].fields.items():
            if not field.value:
                labels.add(key, None, None)
            else:
                polygon = field.bounding_regions[0].polygon
                points = list[float]()
                for point in polygon:
                    points.append(point.x)
                    points.append(point.y)
                labels.add(key, str(field.content), BoundingBox.from_flat_list(points))
        return labels


class ModelTrainer(Protocol):
    """Train a model."""

    @abstractmethod
    def train(self, name: str, path: str) -> str:
        """Train a model with the documents at the given path.

        Args:
            name: name of the model
            path: path to the training data

        Returns:
            Model ID
        """
        ...


class AzureModelTrainer(ModelTrainer):
    def __init__(
        self,
        admin_client: DocumentModelAdministrationClient,
        storage_client: AzureFileIO,
        fields_json: str = "fields.json",
    ):
        """Initialize the trainer.

        Args:
            admin_client: DocumentModelAdministrationClient instance
            storage_client: AzureFileIO instance
        """
        self.admin_client = admin_client
        self.storage_client = storage_client
        self.fields_json = fields_json
        if not storage_client.exists(fields_json):
            raise ValueError("Missing fields.json file in storage container")

    def train(
        self,
        name: str,
        path: str,
    ) -> str:
        """Train a model with the documents at the given URL.

        Args:
            name: name of the model
            path: path to the training data

        Returns:
            Model ID
        """
        logger.info(
            f"Training model {name} with documents in "
            f"{self.storage_client.container_url} at {path}"
        )

        # Copy the fields.json file to the training data path
        self.storage_client.copy(
            self.fields_json, self.storage_client.join(path, "fields.json")
        )

        # Begin training
        poller = self.admin_client.begin_build_document_model(
            description="Custom narrative extraction model",
            model_id=name,
            build_mode=ModelBuildMode.NEURAL,
            blob_container_url=self.storage_client.container_url,
            prefix=path,
        )

        logger.info("Waiting for training to complete...")
        model = poller.result()
        logger.info(f"Training complete. Model ID: {model.model_id}")
        return model.model_id
