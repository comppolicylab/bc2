import logging

from .example import ExampleDoc
from .io import FileReader

logger = logging.getLogger(__name__)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
    logging.WARNING
)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def evaluate(fr: FileReader, base_path: str):
    """Evaluate the model on the given data.

    Args:
        fr: A FileReader instance.
        base_path: The base path to the data.
    """
    all_files = list(fr.list(base_path))

    # Filter to files that have OCR and labels.
    pdfs = set[str]()
    has_labels = set[str]()
    has_ocr = set[str]()

    for name in all_files:
        if name.endswith(".pdf"):
            pdfs.add(name)
        elif name.endswith(".labels.json"):
            pdf_name = name[: -len(".labels.json")]
            has_labels.add(pdf_name)
        elif name.endswith(".ocr.json"):
            pdf_name = name[: -len(".ocr.json")]
            has_ocr.add(pdf_name)
    files_to_process = list(pdfs.intersection(has_labels).intersection(has_ocr))

    logger.info(f"Found {len(files_to_process)} files in {base_path}")

    # Process the first 4 files for testing
    for name in files_to_process[:4]:
        logger.info(f"Processing {name}")
        doc = ExampleDoc.load(fr, name)
        print(doc.labels)
