import re

from .common import Renderer, format_narrative, TITLE, DISCLAIMER


def render_text(out: str, narrative: str, original: str | None = None) -> None:
    """Render a narrative to text.

    Args:
        out: The path to the output file.
        narrative: The narrative to render
        original: The original narrative, if available.
    """
    with open(out, "w") as f:
        f.write(TITLE)
        f.write("\n\n")
        # Strip HTML tags from the normal disclaimer
        f.write(re.sub(r"<[^>]*>", "", DISCLAIMER))
        f.write("\n\n")
        f.write("=== NARRATIVE ===\n")
        # TODO: might want to add some formatting for the diff
        f.write(format_narrative(lambda x, y: x,
                                 lambda x: f"{x}\n\n",
                                 lambda x: x,
                                 narrative,
                                 original))
        f.write("=== END OF DOCUMENT ===\n")


text = Renderer("text", "txt", render_text)
