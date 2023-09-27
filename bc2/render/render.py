from .backends import get_renderer, register
from .html import html
from .pdf import pdf
from .text import text

for renderer in [pdf, html, text]:
    register(renderer)


def render(fmt: str, out: str, narrative: str, original: str | None = None) -> None:
    """Render a narrative to a file.

    Args:
        fmt: The format to render to.
        out: The path to the output file.
        narrative: The narrative to render
        original: The original narrative, if available.
    """
    renderer = get_renderer(fmt)
    renderer.render(out, narrative, original)


def ensure_filename_matches_format(fmt: str, filename: str) -> str:
    """Ensure filename has the correct extension for the given format.

    Args:
        fmt: The format to render to.
        filename: The filename of the narrative.

    Returns:
        The filename for the narrative in the given format.
    """
    renderer = get_renderer(fmt)
    # Get the filename without the extension
    filename = filename.rsplit(".", 1)[0]
    # Add in the correct format extension (might be the same as the original)
    return f"{filename}.{renderer.extension}"
