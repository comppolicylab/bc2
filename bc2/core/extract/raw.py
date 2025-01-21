from functools import cached_property
from typing import Literal

from pydantic import BaseModel

from ..common.file import MemoryFile
from .base import BaseExtractDriver, register_preprocessor


class RawExtractConfig(BaseModel):
    engine: Literal["extract:raw"]

    @cached_property
    def driver(self) -> "RawExtractDriver":
        return RawExtractDriver(self)


class RawExtractDriver(BaseExtractDriver[str]):
    """Extract raw text from a file."""

    def __init__(self, config: RawExtractConfig) -> None:
        self.config = config

    def extract(self, data: str) -> str:
        return data

    @register_preprocessor("^text/*")
    def format_text(self, file: MemoryFile) -> str:
        return file.buffer.getvalue().decode("utf-8")
