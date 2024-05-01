import json
import logging
import os
import sys

import click

import bc2.llm as llm
import bc2.render as render

from .cache import get_cache_path
from .config import config
from .extract import extract_narrative_from_pdf
from .infer import infer_annotations

logging.basicConfig(level=config.log_level)
logger = logging.getLogger(__name__)


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
        if narr_path and os.path.exists(narr_path):
            with open(narr_path, "r") as f:
                og_narr = f.read()
        # Only return cached result if it's valid
        if text == og_narr and cache_path and os.path.exists(cache_path):
            with open(cache_path, "r") as f:
                return f.read()

    redaction = llm.redact_with_chat(text)
    if cache_path and narr_path:
        with open(narr_path, "w") as f:
            f.write(text)
        with open(cache_path, "w") as f:
            f.write(redaction)

    return redaction


@click.group()
def cli() -> None:
    """Redact text using the Blind Charging language model."""
    pass


@cli.command("redact")
@click.argument("path", required=False, default=None)
@click.option("--json/--no-json", "return_json", default=False)
def redact(path: str | None, return_json: bool) -> None:
    """Redact text, either from a file or stdin.

    Args:
        path (str | None): Path to the file to redact. If None, use stdin.
    """
    text = ""
    if path is None:
        text = sys.stdin.read()
    else:
        with open(path, "r") as f:
            text = f.read()
    redacted = redact_text(text)
    if return_json:
        annotations = list(infer_annotations(text, redacted))
        sys.stdout.write(json.dumps(annotations))
    else:
        sys.stdout.write(redacted)


@cli.command("run")
@click.argument("path")
@click.option("--model", default=config.bc2.document_model)
@click.option("--output-dir", default=config.bc2.output_dir)
@click.option("--cache/--no-cache", default=True)
@click.option("--cache-dir", default=config.bc2.cache_dir)
@click.option("--output", default=None)
@click.option("--renderer", default=config.bc2.renderer)
@click.option("--narrative-field", default=config.bc2.extraction.narrative_field)
@click.option("--min-confidence", default=config.bc2.extraction.min_confidence)
def run(
    path: str,
    model: str,
    output_dir: str,
    cache: bool,
    cache_dir: str = "",
    output: str | None = None,
    renderer: str = "pdf",
    narrative_field: str = "narrative",
    min_confidence: float = 0.04,
) -> None:
    """Run document analysis on a PDF.

    Args:
        path (str): Path to the PDF to analyze.
        model (str): Model to use for analysis.
        output_dir (str): Path to the directory to save results to.
        cache (bool): Whether to cache results / use cached results.
        cache_dir (str): Path to the directory to cache results in.
        output (str | None): Path to save the redacted PDF to.
        renderer (str): Renderer(s) to use for output. To use multiple, separate with commas.
        narrative_field (str): Field to extract the narrative from.
        min_confidence (float): Minimum confidence to accept for extraction.
    """
    logger.info("Loading Blind Charging redaction tool ...")
    cached: str | None = None
    if cache and not cache_dir:
        logger.warning("No cache directory specified, disabling cache.")
        cached = None
    elif cache:
        cached = None if not cache else get_cache_path(cache_dir, path, model)

    narrative = extract_narrative_from_pdf(
        path,
        model=model,
        cached=cached,
        narrative_field=narrative_field,
        min_confidence=min_confidence,
    )
    if not narrative:
        logger.error("Failed to extract narrative from PDF.")
        return

    logger.info("Redacting narrative with language model ...")
    redacted = redact_text(narrative, cached=cached)

    logger.info("Rendering redacted narrative ...")

    # Output location can be either string or file-like stream
    redact_path = "redacted.pdf"
    if output:
        redact_path = output
    else:
        if output_dir:
            # Ensure that the directory exists
            os.makedirs(output_dir, exist_ok=True)
            # Get a default filename with a `.redacted.pdf` suffix:
            output_name = os.path.splitext(os.path.basename(path))[0] + ".redacted.pdf"
            redact_path = os.path.join(output_dir, output_name)
            logger.debug("Using output directory %s", output_dir)
        else:
            logger.warning(
                "No output location specified, using default: %s", redact_path
            )

    for fmt in renderer.split(","):
        # Make sure that the extension is correct, fixing it if necessary
        render_path = render.ensure_filename_matches_format(fmt, redact_path)
        logger.info(f"Rendering redacted narrative as {fmt} to {render_path} ...")
        render.render(fmt, render_path, redacted, original=narrative)

    logger.info("Done!")


if __name__ == "__main__":
    cli()
