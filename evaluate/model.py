import functools
import json
import logging
import os
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, Protocol

from azure.ai.formrecognizer import (
    BlobFileListSource,
    ClassifierDocumentTypeDetails,
    DocumentAnalysisClient,
    DocumentModelAdministrationClient,
    ModelBuildMode,
)
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential

from .io import AzureFileIO
from .label import BoundingBox, Labels

logger = logging.getLogger(__name__)


ModelType = Literal["classifier", "extractor"]


# Default number of threads to use for requests.
DEFAULT_THREAD_COUNT = (os.cpu_count() or 1) + 4


@dataclass
class ModelInfo:
    """Information about a model."""

    id: str
    type: ModelType
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

    def list_models(self, type_: ModelType) -> list[ModelInfo]:
        """List models."""
        models = (
            self.dmac.list_document_models()
            if type_ == "extractor"
            else self.dmac.list_document_classifiers()
        )
        return [
            ModelInfo(
                id=m.model_id if type_ == "extractor" else m.classifier_id,
                type=type_,
                description=m.description,
                tags=m.tags if type_ == "extractor" else None,
                created_on=m.created_on,
                expires_on=m.expires_on,
                api_version=m.api_version,
            )
            for m in models
        ]

    def model_exists(self, type_: ModelType, id_: str) -> bool:
        """Check if a model exists."""
        model = self.get_model(type_, id_)
        return model is not None

    def get_model(self, type_: ModelType, id_: str) -> ModelInfo | None:
        """Get a model."""
        try:
            m = (
                self.dmac.get_document_model(model_id=id_)
                if type_ == "extractor"
                else self.dmac.get_document_classifier(classifier_id=id_)
            )
            return ModelInfo(
                id=m.model_id if type_ == "extractor" else m.classifier_id,
                type=type_,
                description=m.description,
                tags=m.tags if type_ == "extractor" else None,
                created_on=m.created_on,
                expires_on=m.expires_on,
                api_version=m.api_version,
            )
        except ResourceNotFoundError:
            return None


class ModelRunner(Protocol):
    """Run a model."""

    @abstractmethod
    def classify(self, classifier_id: str, path: str) -> str:
        """Run a model on the documents at the given path.

        Args:
            model_id: ID of the model
            path: path to the documents

        Returns:
            Predicted document type
        """
        ...

    @abstractmethod
    def extract(self, model_id: str, path: str) -> Labels:
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

    def classify(self, classifier_id: str, doc: str) -> str:
        """Run a model on the documents at the given path.

        Args:
            classifier_id: ID of the model
            doc: document path

        Returns:
            Predicted document type
        """
        logger.info(
            f"Running model {classifier_id} on {doc} in " f"{self.store.container_url}"
        )

        url = self.store.join(self.store.container_url, doc)

        poller = self.cli.begin_classify_document_from_url(
            classifier_id=classifier_id,
            document_url=url,
        )

        logger.info("Waiting for model run to complete...")
        result = poller.result()
        logger.info("Model run complete.")
        if len(result.documents) != 1:
            raise ValueError("Expected exactly one document in result")
        return result.documents[0].doc_type

    def extract(self, model_id: str, doc: str) -> Labels:
        """Run a model on the documents at the given path.

        Args:
            model_id: ID of the model
            doc: document path

        Returns:
            Fields identified in the document
        """
        logger.info(
            f"Running model {model_id} on {doc} in " f"{self.store.container_url}"
        )

        url = self.store.join(self.store.container_url, doc)

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

    def multi_run(
        self,
        type_: ModelType,
        model_id: str,
        docs: list[str],
        threads: int = DEFAULT_THREAD_COUNT,
    ) -> dict[str, Any]:
        """Run a model on the documents at the given path.

        Args:
            type_: type of model
            model_id: ID of the model
            docs: list of document paths
            threads: number of threads to use

        Returns:
            Result of running the model
        """
        f = self.classify if type_ == "classifier" else self.extract
        run = functools.partial(f, model_id)
        results: dict[str, Any] = {}

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(run, doc): doc for doc in docs}
            for future in as_completed(futures):
                doc = futures[future]
                try:
                    results[doc] = future.result()
                except Exception as exc:
                    logger.error(f"{doc} generated an exception: {exc}")

        return results


class ModelTrainer(Protocol):
    """Train a model."""

    @abstractmethod
    def train_extractor(
        self,
        name: str,
        *,
        description: str,
        path: str | None,
        docs: list[str] | None,
        tags: dict[str, str] | None,
    ) -> str:
        """Train a model with the documents at the given path.

        Args:
            name: name of the model
            description: description of the model
            path: path to the training data
            docs: list of documents to train on
            tags: tags to apply to the model

        Returns:
            Model ID
        """
        ...

    @abstractmethod
    def train_classifier(
        self,
        name: str,
        *,
        description: str,
        files: list[str],
        labels: list[str],
    ) -> str:
        """Train a model with the documents at the given path.

        Args:
            name: name of the model
            description: description of the model
            path: path to the training data
            files: list of files to train on
            labels: list of labels corresponding to files

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

    def train_classifier(
        self,
        name: str,
        *,
        description: str,
        files: list[str],
        labels: list[str],
    ) -> str:
        """Train a model with the documents at the given URLs.

        Args:
            name: name of the model
            description: description of the model
            files: list of document paths to use in training
            labels: list of labels for the documents (in the same order)

        Returns:
            Model ID
        """
        logger.info(
            f"Training extraction model {name} with documents in "
            f"{self.storage_client.container_url}"
        )

        if files is None or labels is None:
            raise ValueError("Both files and labels must be specified")

        if len(files) != len(labels):
            raise ValueError("Files and labels must be the same length")

        # Write list of documents as a JSONL file.
        labeled = dict[str, ClassifierDocumentTypeDetails]()

        # Process labels to reduce into a dict of lists
        docs = dict[str, list[str]]()
        for doc, label in zip(files, [str(lbl) for lbl in labels]):
            if label not in docs:
                docs[label] = []
            docs[label].append(doc)

        # Now write lists of documents to JSONL files in the blob storage
        for label, doclist in docs.items():
            logger.info("Writing list of documents to JSONL file ...")
            docf = f"{name}-{label}-classifier.train.jsonl"
            self.storage_client.write(
                docf, "\n".join(json.dumps({"file": d}) for d in doclist)
            )
            labeled[label] = ClassifierDocumentTypeDetails(
                source=BlobFileListSource(
                    container_url=self.storage_client.container_url,
                    file_list=docf,
                ),
            )

        # Train the model
        try:
            poller = self.admin_client.begin_build_document_classifier(
                doc_types=labeled,
                classifier_id=name,
                description=description,
            )

            logger.info("Waiting for training to complete...")
            model = poller.result()
        except Exception as e:
            logger.error("Training failed.")
            # Clean up the files we created
            for v in labeled.values():
                self.storage_client.delete(v.source.file_list)
            raise e
        logger.info(f"Training complete. Model ID: {model.classifier_id}")
        return model.classifier_id

    def train_extractor(
        self,
        name: str,
        *,
        description: str,
        path: str | None = None,
        docs: list[str] | None = None,
        tags: dict[str, str] | None = None,
    ) -> str:
        """Train a model with the documents at the given URL.

        Args:
            name: name of the model
            description: description of the model
            path: path to the training data
            docs: list of document names to train on
            tags: tags for the model

        Returns:
            Model ID
        """
        logger.info(
            f"Training extraction model {name} with documents in "
            f"{self.storage_client.container_url}"
        )

        if path is None and docs is None:
            raise ValueError("Either path or docs must be specified")

        if path is not None and docs is not None:
            raise ValueError("Only one of path or docs may be specified")

        # Azure uses a "prefix" not a path, per se. We enforce path.
        if path is not None:
            if not path.endswith("/"):
                logger.warning("Path should end with /")
                path += "/"
            # Copy the fields.json file to the training data path
            self.storage_client.copy(
                self.fields_json, self.storage_client.join(path, "fields.json")
            )

        # Write list of documents as a JSONL file.
        # Format is not documented, but an example is here:
        # https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept-custom-classifier?view=doc-intel-4.0.0#training-a-model
        doc_list = f"{name}-extractor.train.jsonl"
        if docs:
            logger.info("Writing list of documents to JSONL file ...")
            self.storage_client.write(
                doc_list, "\n".join(json.dumps({"file": d}) for d in docs)
            )

        # Begin training
        try:
            poller = self.admin_client.begin_build_document_model(
                description=description,
                model_id=name,
                build_mode=ModelBuildMode.NEURAL,
                blob_container_url=self.storage_client.container_url,
                prefix=path,
                file_list=doc_list if docs else None,
                tags=tags,
            )

            logger.info("Waiting for training to complete...")
            model = poller.result()
            logger.info(f"Training complete. Model ID: {model.model_id}")
        except Exception as e:
            logger.error("Training failed.")
            if docs:
                self.storage_client.delete(doc_list)
            raise e
        return model.model_id
