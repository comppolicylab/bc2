from functools import cached_property
from typing import Literal

from ..common.file import MemoryFile
from ..common.image import ImageUrl
from ..common.openai import OpenAIChatConfig, OpenAIConfig
from ..common.pdf import pdf2imgs
from .base import BaseExtractDriver, register_preprocessor


class OpenAIExtractConfig(OpenAIConfig):
    """OpenAI Extract config."""

    engine: Literal["extract:openai"]
    generator: OpenAIChatConfig

    @cached_property
    def driver(self) -> "OpenAIExtractDriver":
        return OpenAIExtractDriver(self)


class OpenAIExtractDriver(BaseExtractDriver[list[ImageUrl]]):
    def __init__(self, config: OpenAIExtractConfig):
        self.config = config
        self.client = config.client.init()

    @register_preprocessor(r"^image/.*")
    def convert_image(self, file: MemoryFile) -> list[ImageUrl]:
        return [ImageUrl(url=file.data_url())]

    @register_preprocessor(r"^application/pdf")
    def convert_pdf(self, file: MemoryFile) -> list[ImageUrl]:
        imgs = list[ImageUrl]()
        file.buffer.seek(0)
        for img_bytes in pdf2imgs(file.buffer):
            img_file = MemoryFile(img_bytes)
            imgs.append(ImageUrl(url=img_file.data_url()))
        return imgs

    def extract(self, input: list[ImageUrl]) -> str:
        """Generate a completion optionally including image input."""
        return self.config.generator.invoke(self.client, input)
