import base64
from functools import cached_property
from typing import Literal, Tuple

from ..common.file import MemoryFile
from ..common.image import ImageUrl
from ..common.openai import OpenAIChatConfig, OpenAIConfig
from ..common.pdf import pdf2imgs
from ..common.preprocess import register_preprocessor
from .base import BaseExtractDriver


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
        # `pdf2imgs` renders one page at a time as PNG. Encode each page's
        # bytes directly into a data URL rather than wrapping it in a throwaway
        # MemoryFile and copying via content()/getvalue(). Only the resulting
        # base64 strings are retained (they must all be sent in one request);
        # each page's raw bytes are released as the loop advances.
        for img_bytes in pdf2imgs(file.buffer):
            encoded = base64.b64encode(img_bytes).decode()
            imgs.append(ImageUrl(url=f"data:image/png;base64,{encoded}"))
        return imgs

    # TODO(jnu): support for text/* and potentially other types.
    # We might want to return simple text files directly, but we
    # could send more complicated types like text/html to OpenAI
    # for extraction of the actual text content.

    def extract(self, input: list[ImageUrl]) -> Tuple[str, bool]:
        """Generate a completion optionally including image input."""
        result = self.config.generator.invoke(self.client, input)
        return result.content, result.is_truncated
