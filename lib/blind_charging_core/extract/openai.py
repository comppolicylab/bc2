from functools import cached_property
from typing import Literal

from pydantic import BaseModel

from ..common.file import MemoryFile
from ..common.openai import OpenAIApiConfig
from ..common.text import Text
from .base import BaseExtractDriver


class OpenAIExtractConfig(BaseModel):
    """OpenAI Extract config."""

    engine: Literal["extract:openai"]
    api: OpenAIApiConfig
    model: str
    prompt_file: str

    @cached_property
    def driver(self) -> "OpenAIExtractDriver":
        return OpenAIExtractDriver(self)


class OpenAIExtractDriver(BaseExtractDriver):
    def __init__(self, config: OpenAIExtractConfig):
        self.config = config

    def __call__(self, file: MemoryFile) -> Text:
        raise NotImplementedError("OpenAIExtractDriver not implemented yet!")
