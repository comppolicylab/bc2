import logging

from .docs import get_true_labels, list_docs
from .io import AzureFileIO, LocalFileIO
from .model import AzureModelClient
from .render import render_bounds

logger = logging.getLogger(__name__)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
    logging.WARNING
)
logging.getLogger("urllib3").setLevel(logging.WARNING)


__all__ = [
    "get_true_labels",
    "list_docs",
    "AzureFileIO",
    "LocalFileIO",
    "AzureModelClient",
    "render_bounds",
]
