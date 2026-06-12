from io import BytesIO
from typing import Generator

import pymupdf


def pdf2imgs(
    input: BytesIO, format: str = "png", dpi: int | None = None, **kwargs
) -> Generator[bytes, None, None]:
    """Render a PDF page to a set of images.

    By default, the image is rendered as a PNG.

    Args:
        input: The PDF bytes to render.
        format: The image format to encode each page as.
        dpi: Optional render resolution. Higher DPI produces larger rasters
            (and more memory per page); leaving this unset uses pymupdf's
            default resolution. Lowering it is the main lever for reducing
            per-page memory when extraction quality allows.

    Additional keyword arguments are passed to the PIL image encoder.

    Yields bytes of the image for each page in the PDF. Each page's pixmap is
    released before the next page is rendered, so only one page's raster is
    held in memory at a time.
    """
    pdf = pymupdf.open(stream=input, filetype="pdf")
    try:
        for page in pdf:
            pixmap = page.get_pixmap(dpi=dpi) if dpi is not None else page.get_pixmap()
            try:
                yield pixmap.pil_tobytes(format=format, **kwargs)
            finally:
                # Drop the pixmap (and its pixel buffer) before advancing so we
                # don't accumulate rasters across pages.
                pixmap = None
    finally:
        pdf.close()
