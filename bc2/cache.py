import hashlib
import os


def get_cache_path(
    cache_dir: str,
    document_path: str,
    model: str,
) -> str:
    """Get the path to save the analysis result to.

    Args:
        cache_path (str): Path to the cache directory.
        document_path (str): Path to the PDF to analyze.
        model (str): Model to use for analysis.

    Returns:
        str: Path to save the analysis result to.
    """
    # Compute sha256 hash of the document at the specified path.
    document_hash = hashlib.sha256(document_path.encode()).hexdigest()
    # Get a human-readable name that includes parts of the original filename,
    # along with the content hash:
    #   - Get the filename without the extension
    #   - Truncate the filename to 10 characters
    #   - Append the first 7 chars of the content hash
    fn = os.path.splitext(os.path.basename(document_path))[0]
    # Clean up the filename by removing any non-alphanumeric characters.
    fn = "".join(filter(str.isalnum, fn))
    # Truncate the filename to 16 characters.
    fn = fn[:32]
    fn += f"_{document_hash[:7]}"
    # Join the cache directory with the cache name and the model name.
    return os.path.join(cache_dir, fn, model)
