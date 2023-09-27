import json
import os

import click
from azure.ai.formrecognizer import AnalyzeResult, DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from pypdf import PdfReader
from tqdm import tqdm

from .config import config

document_analysis_client = DocumentAnalysisClient(
    endpoint=config.azure.endpoint,
    credential=AzureKeyCredential(config.azure.key),
)


def get_output_path(
    document_path: str,
    document_dir: str,
    output_dir: str | None,
    model: str,
) -> str | None:
    """Get the path to save the analysis result to.

    Args:
        document_path (str): Path to the PDF to analyze.
        document_dir (str): Path to the directory containing the PDF.
        output_dir (str | None): Path to the directory to save results to.
        model (str): Model to use for analysis.

    Returns:
        str | None: Path to save the analysis result to.
    """
    if output_dir is None:
        return None
    return os.path.join(
        output_dir,
        model,
        os.path.relpath(
            document_path,
            document_dir,
        ).replace(".pdf", ""),
    )


def analyze_document(
    document_path: str,
    model: str = "prebuilt-read",
    cached: str | None = None,
    use_cache: bool = True,
) -> list[AnalyzeResult]:
    """Run a PDF through Azure document analysis.

    Args:
        document_path (str): Path to the PDF to analyze.
        model (str): Model to use for analysis.
        cached (str | None): Path to file where cached results are stored.

    Returns:
        list[AnalyzeResult]: Results from Azure document analysis.
    """
    # We analyze each page separately because the FormRecognizer API doesn't
    # currently fully support entire document analysis. It just analyzes two
    # pages at a time, even if you request more.
    pages = len(PdfReader(document_path).pages)
    results: list[AnalyzeResult] = [None] * pages

    # Check if the result is cached, and return it if it is.
    if cached is not None:
        if os.path.exists(cached):
            for i in range(pages):
                try:
                    page_path = os.path.join(cached, f"{i + 1}.json")
                    with open(page_path, "r") as f:
                        results[i] = AnalyzeResult.from_dict(json.load(f))
                except FileNotFoundError:
                    pass
        else:
            os.makedirs(cached, exist_ok=True)

    # Run analysis on the document using the remote service.
    for i in range(pages):
        if results[i] is None:
            with open(document_path, "rb") as f:
                poller = document_analysis_client.begin_analyze_document(
                    model,
                    document=f,
                    locale="en-US",
                    pages=f"{i + 1}",
                )
                results[i] = poller.result()
            if cached is not None:
                page_path = os.path.join(cached, f"{i + 1}.json")
                with open(page_path, "w") as f:
                    f.write(json.dumps(results[i].to_dict()))

    return results


@click.group()
@click.option("--model", default="prebuilt-read")
@click.pass_context
def main(ctx: click.Context, model: str):
    """Analyze PDFs with Azure Form Recognizer.

    Args:
        ctx (click.Context): Click context.
        model (str): Model to use for analysis.
    """
    ctx.ensure_object(dict)
    ctx.obj["model"] = model


@main.command()
@click.argument("document_dir")
@click.argument("output_dir")
@click.pass_context
def walk(ctx: click.Context, document_dir: str, output_dir: str):
    """Analyze all PDFs in the provided directory.

    Args:
        ctx (click.Context): Click context.
        document_dir (str): Path to the directory containing PDFs to analyze.
        output_dir (str): Path to the directory to save results to.
    """
    model = ctx.obj["model"]
    # Build a queue of PDFs to process.
    queue = list[tuple[str, str]]()
    for root, dirs, files in os.walk(document_dir):
        for file in files:
            if file.endswith(".pdf"):
                file_path = os.path.join(root, file)
                # Mimic the same directory structure from `document_dir` in
                # `output_dir`. E.g. `document_dir/foo/bar.pdf` will be saved
                # as `output_dir/foo/bar.json`.
                output_path = get_output_path(
                    file_path, document_dir, output_dir, model
                )
                queue.append((file_path, output_path))

    # Process the queue with a progress bar.
    for file_path, output_path in tqdm(queue):
        # Ensure that the directory exists.
        os.makedirs(output_path, exist_ok=True)
        # Run analysis and cache result
        analyze_document(file_path, model=model, cached=output_path)


@main.command()
@click.argument("document_path")
@click.argument("output_dir")
@click.pass_context
def analyze(ctx: click.Context, document_path: str, output_dir: str):
    """Analyze a single document at the provided path.

    Args:
        ctx (click.Context): Click context.
        document_path (str): Path to the PDF to analyze.
        output_dir (str): Path to the directory to save results to.
    """
    analyze_document(document_path, model=ctx.obj["model"], cached=output_dir)


if __name__ == "__main__":
    main()
