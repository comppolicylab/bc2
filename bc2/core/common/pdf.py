from io import BytesIO
from typing import Generator

import pymupdf


def pdf2imgs(
    input: BytesIO, format: str = "png", **kwargs
) -> Generator[bytes, None, None]:
    """Render a PDF page to a set of images.

    By default, the image is rendered as a PNG.

    Additional keyword arguments are passed to the PIL image encoder.

    Yields bytes of the image for each page in the PDF.
    """
    pdf = pymupdf.open(stream=input, filetype="pdf")
    for page in pdf:
        pixmap = page.get_pixmap()
        yield pixmap.pil_tobytes(format=format, **kwargs)
