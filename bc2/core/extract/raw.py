from functools import cached_property
from typing import Literal, Tuple

from pydantic import BaseModel

from ..common.file import MemoryFile
from ..common.preprocess import register_preprocessor
from .base import BaseExtractDriver


class RawExtractConfig(BaseModel):
    engine: Literal["extract:raw"]

    @cached_property
    def driver(self) -> "RawExtractDriver":
        return RawExtractDriver(self)


class RawExtractDriver(BaseExtractDriver[str]):
    """Extract raw text from a file."""

    def __init__(self, config: RawExtractConfig) -> None:
        self.config = config

    def extract(self, data: str) -> Tuple[str, bool]:
        return data, False

    @register_preprocessor("^text/*")
    def format_text(self, file: MemoryFile) -> str:
        return file.buffer.getvalue().decode("utf-8")

    @register_preprocessor("^application/x-empty")
    def format_empty(self, file: MemoryFile) -> str:
        return ""

    @register_preprocessor("^application/octet-stream")
    def format_binary(self, file: MemoryFile) -> str:
        return file.buffer.getvalue().decode("utf-8", errors="replace")
