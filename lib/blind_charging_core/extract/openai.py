from functools import cached_property
from typing import Literal

from ..common.file import MemoryFile
from ..common.image import ImageUrl
from ..common.openai import OpenAIChatConfig, OpenAIConfig
from ..common.text import Text
from .base import BaseExtractDriver


class OpenAIExtractConfig(OpenAIConfig):
    """OpenAI Extract config."""

    engine: Literal["extract:openai"]
    generator: OpenAIChatConfig

    @cached_property
    def driver(self) -> "OpenAIExtractDriver":
        return OpenAIExtractDriver(self)


class OpenAIExtractDriver(BaseExtractDriver):
    def __init__(self, config: OpenAIExtractConfig):
        self.config = config
        self.client = config.client.init()

    def __call__(self, file: MemoryFile) -> Text:
        # Generate an image from the input file
        images = self.convert(file)
        extraction = self.generate(images)
        return Text(extraction)

    def convert(self, file: MemoryFile) -> list[ImageUrl]:
        """Convert the input file to a set of images."""
        # TODO - might be better to upload files to the API instead of base64 encoding
        if file.mime_type.startswith("image"):
            return [ImageUrl(url=file.data_url())]
        elif file.mime_type == "application/pdf":
            # TODO - render each page as an image
            raise NotImplementedError("PDF extraction not yet implemented")
        else:
            raise ValueError(f"Unsupported file type: {file.mime_type}")

    def generate(self, input: list[ImageUrl]) -> str:
        """Generate a completion optionally including image input."""
        return self.config.generator.invoke(self.client, input)
