import os


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
