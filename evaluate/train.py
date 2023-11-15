import logging

from azure.ai.formrecognizer import DocumentModelAdministrationClient, ModelBuildMode

logger = logging.getLogger(__name__)


def train_model(
    admin_client: DocumentModelAdministrationClient, name: str, train_set: str
) -> str:
    """Train a model with the documents at the given URL.

    Args:
        admin_client: DocumentModelAdministrationClient instance
        name: name of the model
        train_set: blob storage path to documents

    Returns:
        Model ID
    """
    logger.info(f"Training model {name} with documents at {train_set}")
    poller = admin_client.begin_build_document_model(
        description="Custom narrative extraction model",
        model_id=name,
        build_mode=ModelBuildMode.NEURAL,
        blob_container_url=train_set,
    )

    logger.info("Waiting for training to complete...")
    model = poller.result()
    logger.info(f"Training complete. Model ID: {model.model_id}")
    return model.model_id
