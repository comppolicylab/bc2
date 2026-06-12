import io
import random
import tracemalloc
import types
from typing import Callable

import pymupdf
from PIL import Image

from .pdf import pdf2imgs


def _make_noise_pdf(pages: int, size: tuple[int, int] = (300, 300)) -> bytes:
    """Build a multi-page PDF where each page is a random-noise image.

    Random noise produces large, incompressible PNGs so that the per-page
    raster bytes dominate Python-tracked memory and the streaming behaviour is
    actually measurable.
    """
    doc = pymupdf.open()
    rng = random.Random(0)
    try:
        for _ in range(pages):
            noise = rng.randbytes(size[0] * size[1] * 3)
            img = Image.frombytes("RGB", size, noise)
            buf = io.BytesIO()
            img.save(buf, format="png")
            page = doc.new_page(width=size[0], height=size[1])
            page.insert_image(
                pymupdf.Rect(0, 0, size[0], size[1]), stream=buf.getvalue()
            )
        return doc.tobytes()
    finally:
        doc.close()


def _peak_bytes(fn: Callable[[], object]) -> int:
    """Return the peak Python-tracked memory (bytes) while running `fn`."""
    tracemalloc.start()
    try:
        fn()
        _, peak = tracemalloc.get_traced_memory()
        return peak
    finally:
        tracemalloc.stop()


def test_pdf2imgs_is_lazy_generator():
    pdf = _make_noise_pdf(2)
    gen = pdf2imgs(io.BytesIO(pdf))
    assert isinstance(gen, types.GeneratorType)
    first = next(gen)
    assert isinstance(first, bytes)
    gen.close()


def test_pdf2imgs_streams_pages_without_accumulating():
    """Streaming the pages should not hold every page raster at once.

    We compare peak memory when we keep only the current page against keeping
    every page in a list. The streaming peak should be a small fraction of the
    bulk peak, and should not grow with page count.
    """
    pages = 12
    pdf = _make_noise_pdf(pages)

    def stream() -> object:
        last = None
        for img in pdf2imgs(io.BytesIO(pdf)):
            # Only retain the current page; previous pages are released.
            last = img
        return last

    def bulk() -> object:
        return list(pdf2imgs(io.BytesIO(pdf)))

    stream_peak = _peak_bytes(stream)
    bulk_peak = _peak_bytes(bulk)

    # Holding all pages should cost meaningfully more than holding one. Use a
    # generous margin to stay robust against allocator/measurement noise.
    assert stream_peak < bulk_peak / 2
