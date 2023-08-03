import click
from azure.ai.formrecognizer import AnalyzeResult
from azure.ai.formrecognizer._models import DocumentField

from document_analysis import analyze_document, get_output_path
import llm


def extract_narrative_fields(analysis: list[AnalyzeResult]) -> list[DocumentField]:
    """Extract the narrative from the analysis results.

    Args:
        analysis (list[AnalyzeResult]): Results, one for each page
    """
    narratives = list[str]()
    # Look through each page of the analysis results and find any narratives.
    for page in analysis:
        for doc in page.documents:
            narrative = doc.fields.get("narrative")
            if narrative:
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
        if field.value:
            if narrative:
                narrative += "\n\n"
            narrative += field.value
    return narrative


def redact_text(text: str) -> str:
    """Redact sensitive information from text.

    Args:
        text (str): Text to redact.

    Returns:
        str: Redacted text.
    """
    max_len = len(text) * 1.1
    return llm.redact(text, temperature=0, top_p=0.5, max_tokens=max_len)


@click.command()
@click.argument("path")
@click.option("--model", default="bc2-narrative")
@click.option("--document-root", default=".")  # TODO - refactor cache so that this is not needed
@click.option("--cache-dir", default=None)
def run(path: str, model: str, document_root: str, cache_dir: str | None = None):
    """Run document analysis on a PDF.

    Args:
        path (str): Path to the PDF to analyze.
        model (str): Model to use for analysis.
        document_root (str): Path to the root of the document.
        cache_dir (str | None): Path to the directory to cache results in.
    """
    cached = get_output_path(path, document_root, cache_dir, model)
    analysis = analyze_document(path, model=model, cached=cached)
    fields = extract_narrative_fields(analysis)
    narrative = get_narrative(fields)
    redacted = redact_text(narrative)
    print(redacted)


if __name__ == "__main__":
    run()
