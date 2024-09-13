import io
from dataclasses import dataclass
from functools import cached_property
from typing import Literal

import pytesseract
from PIL import Image
from pydantic import BaseModel

from ..common.file import MemoryFile
from ..common.pdf import pdf2imgs
from .base import BaseExtractDriver, register_preprocessor


@dataclass
class WrappedData:
    raw_text: str
    images: list[Image.Image]


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
        images: list[Image.Image] = []
        file.buffer.seek(0)
        for img_bytes in pdf2imgs(file.buffer):
            img = Image.open(io.BytesIO(img_bytes))
            images.append(img)
        return WrappedData(raw_text="", images=images)

    @register_preprocessor(r"^text/.*")
    def convert_text(self, file: MemoryFile) -> WrappedData:
        return WrappedData(raw_text=file.buffer.read().decode(), images=[])

    def extract(self, data: WrappedData) -> str:
        return self._format(data)

    def _format(self, data: WrappedData, separator: str = "\n\n") -> str:
        result = ""
        if data.raw_text:
            result += data.raw_text

        for img in data.images:
            if result:
                result += separator
            result += pytesseract.image_to_string(img, config=self.config.tesseract_cmd)

        return result
