import logging
from abc import abstractmethod
from typing import Protocol

from azure.ai.formrecognizer import (
    DocumentAnalysisClient,
    DocumentModelAdministrationClient,
    ModelBuildMode,
)

from .io import AzureFileIO
from .label import BoundingBox, Labels

logger = logging.getLogger(__name__)


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
