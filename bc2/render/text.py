from .common import Renderer


def render_text(out: str, narrative: str, original: str | None = None) -> None:
    """Render a narrative to text.

    Args:
        out: The path to the output file.
        narrative: The narrative to render
        original: The original narrative, if available.
    """
    # TODO: might want to add some formatting for the diff
    with open(out, "w") as f:
        f.write(narrative)
        f.write("\n")


text = Renderer("text", "txt", render_text)
