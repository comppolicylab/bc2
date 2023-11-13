from datetime import datetime
import logging

from azure.ai.formrecognizer import (
        DocumentModelAdministrationClient,
        ModelBuildMode
        )
from azure.identity import DefaultAzureCredential


logger = logging.getLogger(__name__)


def train(endpoint: str, train_set: str) -> str:
    """Train a model with the documents at the given URL.

    Args:
        endpoint: form recognizer endpoint
        train_set: blob storage path to documents

    Returns:
        Model ID
    """
    credential = DefaultAzureCredential()
    admin_client = DocumentModelAdministrationClient(
        endpoint=endpoint,
        credential=credential
    )

    # Come up with a unique name for the model based on the current time
    # so we don't have to worry about name collisions.
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    model_name = f"bc-{ts}"

    logger.info(f"Training model {model_name} with documents at {train_set}")
    poller = admin_client.begin_build_model(
        description="Custom narrative extraction model",
        model_name=model_name,
        build_mode=ModelBuildMode.UNLABELLED,
        source=train_set
    )

    logger.info("Waiting for training to complete...")
    model = poller.result()
    logger.info(f"Training complete. Model ID: {model.model_id}")
    return model.model_id
