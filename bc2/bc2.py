import json
import logging
import os
import sys

import click

import bc2.llm as llm
import bc2.render as render

from .cache import get_output_path
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
@click.option("--document-root", default=config.bc2.document_root)
@click.option("--cache/--no-cache", default=True)
@click.option("--cache-dir", default=config.bc2.cache_dir)
@click.option("--output", default=None)
@click.option("--renderer", default=config.bc2.renderer)
def run(
    path: str,
    model: str,
    document_root: str,
    cache: bool,
    cache_dir: str | None = None,
    output: str | None = None,
    renderer: str = "pdf",
) -> None:
    """Run document analysis on a PDF.

    Args:
        path (str): Path to the PDF to analyze.
        model (str): Model to use for analysis.
        document_root (str): Path to the root of the document.
        cache (bool): Whether to cache results / use cached results.
        cache_dir (str | None): Path to the directory to cache results in.
        output (str | None): Path to save the redacted PDF to.
        renderer (str): Renderer(s) to use for output. To use multiple, separate with commas.
    """
    logger.info("Loading Blind Charging redaction tool ...")
    if cache and not cache_dir:
        logger.warning("No cache directory specified, disabling cache.")
        cached = None
    cached = (
        None if not cache else get_output_path(path, document_root, cache_dir, model)
    )

    narrative = extract_narrative_from_pdf(path, model=model, cached=cached)
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
        if cached:
            redact_path = os.path.join(cached, "redacted.pdf")
        logger.warning("No output location specified, using default: %s", redact_path)

    for fmt in renderer.split(","):
        # Make sure that the extension is correct, fixing it if necessary
        render_path = render.ensure_filename_matches_format(fmt, redact_path)
        logger.info(f"Rendering redacted narrative as {fmt} to {render_path} ...")
        render.render(fmt, render_path, redacted, original=narrative)

    logger.info("Done!")


if __name__ == "__main__":
    cli()
