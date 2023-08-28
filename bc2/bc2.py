import os
import logging

import click
from azure.ai.formrecognizer import AnalyzeResult
from azure.ai.formrecognizer._models import DocumentField

from config import config
from document_analysis import analyze_document, get_output_path
import llm
import render

logging.basicConfig(level=config.log_level)
logger = logging.getLogger(__name__)


def extract_narrative_fields(
        analysis: list[AnalyzeResult],
        min_confidence: float = 0.04
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
            confidence = getattr(narrative, 'confidence', 0.) or 0.
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


def redact_text(text: str, cached: str | None = None) -> str:
    """Redact sensitive information from text.

    Args:
        text (str): Text to redact.
        cached (str | None): Path to the cached results.

    Returns:
        str: Redacted text.
    """
    narr_name = "narrative.txt"
    cache_name = f"redacted_{llm.get_model_slug()}.txt"
    cache_path = os.path.join(cached, cache_name) if cached is not None else None
    narr_path = os.path.join(cached, narr_name) if cached is not None else None
    if cache_path:
        # Check if the input is actually the same before using cached result
        og_narr = ""
        if os.path.exists(narr_path):
            with open(narr_path, "r") as f:
                og_narr = f.read()
        # Only return cached result if it's valid
        if text == og_narr and os.path.exists(cache_path):
            with open(cache_path, "r") as f:
                return f.read()

    redaction = llm.redact_with_chat(text)
    if cache_path:
        with open(narr_path, "w") as f:
            f.write(text)
        with open(cache_path, "w") as f:
            f.write(redaction)

    return redaction


@click.command()
@click.argument("path")
@click.option("--model", default=config.bc2.document_model)
@click.option("--document-root", default=config.bc2.document_root)
@click.option("--cache-dir", default=config.bc2.cache_dir)
def run(path: str,
        model: str,
        document_root: str,
        cache_dir: str | None = None):
    """Run document analysis on a PDF.

    Args:
        path (str): Path to the PDF to analyze.
        model (str): Model to use for analysis.
        document_root (str): Path to the root of the document.
        cache_dir (str | None): Path to the directory to cache results in.
    """
    logger.info("Loading Blind Charging redaction tool ...")
    cached = get_output_path(path, document_root, cache_dir, model)
    logger.info(f"Running analysis on {path} with model {model} ...")
    analysis = analyze_document(path, model=model, cached=cached)
    logger.info("Inspecting analysis result to find narrative(s) ...")
    fields = extract_narrative_fields(analysis)
    if not fields:
        logger.warning("No narrative found in document!")
        return
    narrative = get_narrative(fields)
    logger.info("Redacting narrative with language model ...")
    redacted = redact_text(narrative, cached=cached)
    logger.info("Rendering redacted narrative ...")
    redact_path = os.path.join(cached, "redacted.pdf")
    render.pdf(
            redact_path,
            redacted,
            original=narrative)
    logger.info(f"Redacted narrative saved to {redact_path}")
    logger.info("Done!")


if __name__ == "__main__":
    run()
