from typing import TextIO
import json
import os
from sys import stdout

from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient, AnalyzeResult
import click
from tqdm import tqdm

from config import config


document_analysis_client = DocumentAnalysisClient(
    endpoint=config.azure_endpoint,
    credential=AzureKeyCredential(config.azure_key),
    )


def analyze_document(
        document_path: str,
        model: str = "prebuilt-read",
        ) -> AnalyzeResult:
    """Run a PDF through Azure document analysis.

    Args:
        document_path (str): Path to the PDF to analyze.

    Returns:
        dict: Results from Azure document analysis.
    """
    with open(document_path, "rb") as f:
        poller = document_analysis_client.begin_analyze_document(
            model,
            document=f,
            locale="en-US",
            )
        result = poller.result()

    return result


def save_result(result: AnalyzeResult, out: TextIO):
    """Save analysis result to output path.

    Args:
        result (AnalyzeResult): Result from Azure document analysis.
        out (TextIO): Stream to save results to.
    """
    out.write(json.dumps(result.to_dict()))


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
                output_path = os.path.join(
                    output_dir,
                    model,
                    os.path.relpath(
                        file_path,
                        document_dir,
                    ).replace(".pdf", ".json"),
                )

                queue.append((file_path, output_path))

    # Process the queue with a progress bar.
    for file_path, output_path in tqdm(queue):
        # Ensure that the directory exists.
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Run analysis
        result = analyze_document(file_path, model=model)
        # Save result
        with open(output_path, "w") as f:
            save_result(result, f)


@main.command()
@click.argument("document_path")
@click.pass_context
def analyze(ctx: click.Context, document_path: str):
    """Analyze a single document at the provided path.

    Args:
        ctx (click.Context): Click context.
        document_path (str): Path to the PDF to analyze.
    """
    result = analyze_document(document_path, model=ctx.obj["model"])
    save_result(result, stdout)


if __name__ == "__main__":
    main()
