import io
from dataclasses import dataclass, field
from functools import cached_property
from typing import Iterable, Iterator, Literal, Tuple

import pytesseract
from PIL import Image
from pydantic import BaseModel

from ..common.file import MemoryFile
from ..common.pdf import pdf2imgs
from ..common.preprocess import register_preprocessor
from .base import BaseExtractDriver


@dataclass
class WrappedData:
    raw_text: str
    # An iterable (often a lazy generator) of page images. Keeping this lazy
    # lets us OCR one page at a time instead of materializing every page of a
    # document in memory simultaneously.
    images: Iterable[Image.Image] = field(default_factory=list)


class TesseractExtractConfig(BaseModel):
    engine: Literal["extract:tesseract"]

    tesseract_cmd: str | None = None

    @cached_property
    def driver(self) -> "TesseractExtractDriver":
        return TesseractExtractDriver(self)


class TesseractExtractDriver(BaseExtractDriver[WrappedData]):
    def __init__(self, config: TesseractExtractConfig) -> None:
        self.config = config
        if self.config.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_cmd

    @register_preprocessor(r"^image/.*")
    def convert_image(self, file: MemoryFile) -> WrappedData:
        img = Image.open(file.buffer)
        return WrappedData(raw_text="", images=[img])

    @register_preprocessor(r"^application/pdf")
    def convert_pdf(self, file: MemoryFile) -> WrappedData:
        file.buffer.seek(0)
        return WrappedData(raw_text="", images=self._iter_pdf_images(file))

    def _iter_pdf_images(self, file: MemoryFile) -> Iterator[Image.Image]:
        """Lazily yield one rendered page image at a time.

        The image (and its backing per-page bytes) is released as the consumer
        advances, so only a single page is held in memory at once.
        """
        for img_bytes in pdf2imgs(file.buffer):
            yield Image.open(io.BytesIO(img_bytes))

    @register_preprocessor(r"^text/.*")
    def convert_text(self, file: MemoryFile) -> WrappedData:
        # Decode from a zero-copy view; this also avoids depending on the
        # buffer's current read position.
        return WrappedData(raw_text=str(file.view(), "utf-8"), images=[])

    def extract(self, data: WrappedData) -> Tuple[str, bool]:
        return self._format(data), False

    def _format(self, data: WrappedData, separator: str = "\n\n") -> str:
        parts: list[str] = []
        if data.raw_text:
            parts.append(data.raw_text)

        for img in data.images:
            try:
                parts.append(
                    pytesseract.image_to_string(img, config=self.config.tesseract_cmd)
                )
            finally:
                img.close()

        return separator.join(parts)
