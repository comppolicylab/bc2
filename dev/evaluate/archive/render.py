import base64
import io
from typing import TypedDict

import fitz

from .io import FileIO
from .label import BoundingBox, Point


class Region(TypedDict):
    """A region of a label."""

    label: str | None
    bbox: BoundingBox | str  # "BoundingBox(...)"
    color: str | None


# List of colors to cycle through if none are provided.
_COLORS = [
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
    (1, 1, 0),
    (0, 1, 1),
    (1, 0, 1),
    (0, 0, 0),
    (1, 1, 1),
]


def render_bounds(fr: FileIO, file: str, *bounds: Region, fmt: str = "PNG") -> str:
    """Render the bounding boxes of the given regions.

    NOTE: Assumes doc is only one page!

    Args:
        fr: The file to render the bounding boxes on.
        file: The file to render the bounding boxes on.
        bounds: The regions to render.
        fmt: The format to render the file in.

    Returns:
        The rendered file as a base64-encoded string.
    """
    if not fr.exists(file):
        raise ValueError(f"File {file} does not exist")

    # Get a bytestream of the file
    # TODO - can probably stream from the blob store directly
    doc = io.BytesIO(fr.read_binary(file))
    pdf = fitz.open(stream=doc)
    page = pdf[0]
    # Get width and height of the document
    w, h = page.mediabox[2:]

    env = {"Point": Point, "BoundingBox": BoundingBox}
    for i, b in enumerate(bounds):
        # Parse the bounding boxes if necessary
        raw_bbox = b["bbox"]
        bbox = eval(raw_bbox, {}, env) if isinstance(raw_bbox, str) else raw_bbox

        # Scale the bbox by the width and height
        bbox = bbox.scale(w, h)
        rect = fitz.Rect(*bbox.rect())
        color = b.get("color") or _COLORS[i % len(_COLORS)]

        # Draw the bounding box on the pdf
        page.draw_rect(rect, color=color, width=2)

        label = b.get("label") or ""
        if label:
            # Draw the label on the pdf
            page.insert_text(rect.tl, label, fontsize=10, color=color)

    binary = page.get_pixmap().pil_tobytes(format=fmt)
    # Encode the image as a base64 string
    return base64.b64encode(binary).decode("utf-8")
