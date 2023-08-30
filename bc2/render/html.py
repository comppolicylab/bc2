from .common import Renderer


def render_html(out: str, narrative: str, original: str | None = None) -> None:
    """Render a narrative to an HTML file.

    Args:
        out: The path to the output file.
        narrative: The narrative to render
        original: The original narrative, if available.
    """
    raise NotImplementedError("html renderer not implemented yet")


html = Renderer("html", "html", render_html)
