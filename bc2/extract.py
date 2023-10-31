import logging

from azure.ai.formrecognizer import AnalyzeResult
from azure.ai.formrecognizer._models import DocumentField

from .document_analysis import analyze_document

logger = logging.getLogger(__name__)


def extract_narrative_fields(
    analysis: list[AnalyzeResult], min_confidence: float = 0.04
) -> list[DocumentField]:
    """Extract the narrative from the analysis results.

    Args:
        analysis (list[AnalyzeResult]): Results, one for each page
        min_confidence (float, optional): Minimum confidence to accept
    """
    narratives = list[str]()
    # Look through each page of the analysis results and find any narratives.
    for page in analysis:
        for doc in page.documents:
            narrative = doc.fields.get("narrative")
            confidence = getattr(narrative, "confidence", 0.0) or 0.0
            if narrative and confidence >= min_confidence:
                narratives.append(narrative)
    return narratives


def get_narrative(fields: list[DocumentField]) -> str:
    """Get the narrative from all the narrative fields.

    Args:
        fields (list[DocumentField]): List of narrative fields.

    Returns:
        str: The narrative.
    """
    narrative = ""
    for field in fields:
        if field.content:
            if narrative:
                narrative += "\n\n"
            narrative += field.content
    return narrative


def extract_narrative_from_pdf(
    path: str, *, model: str, cached: str | None = None
) -> str | None:
    """Extract the narrative from a PDF.

    Args:
        path (str): Path to pdf
        model (str): Model to use
        cached (str | None, optional): Path to cached analysis results

    Returns:
        str: The narrative, if one was found.
    """
    logger.info(f"Running analysis on {path} with model {model} ...")
    analysis = analyze_document(path, model=model, cached=cached)

    logger.info("Inspecting analysis result to find narrative(s) ...")
    fields = extract_narrative_fields(analysis)

    if not fields:
        logger.warning("No narrative found in document!")
        return None

    return get_narrative(fields)
