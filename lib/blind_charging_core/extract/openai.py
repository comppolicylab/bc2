from functools import cached_property
from typing import Literal

import pymupdf

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
        """Convert the input file into a format that can be understood by OpenAI.

        Currently only supports images and PDFs. We will upload all documents as images.

        Returns a list of image URLs.
        """
        # TODO - might be better to upload files to the API instead of base64 encoding
        if file.mime_type.startswith("image"):
            return [ImageUrl(url=file.data_url())]
        elif file.mime_type == "application/pdf":
            # TODO - grabbing text from the PDF might be better in some cases
            file.buffer.seek(0)
            pdf = pymupdf.open(stream=file.buffer, filetype="pdf")
            imgs: list[ImageUrl] = []
            for page in pdf:
                url = self._render_pdf_page_to_image(page)
                imgs.append(ImageUrl(url=url))
            return imgs
        else:
            raise ValueError(f"Unsupported file type: {file.mime_type}")

    def generate(self, input: list[ImageUrl]) -> str:
        """Generate a completion optionally including image input."""
        return self.config.generator.invoke(self.client, input)

    def _render_pdf_page_to_image(
        self, page: pymupdf.Page, format: str = "png", **kwargs
    ) -> str:
        """Render a PDF page to an image.

        By default, the image is rendered as a PNG.

        Additional keyword arguments are passed to the PIL image encoder.

        Returns the data URL for the image.
        """
        pixmap = page.get_pixmap()
        img = MemoryFile()
        img.writeb(pixmap.pil_tobytes(format=format, **kwargs))
        return img.data_url()
