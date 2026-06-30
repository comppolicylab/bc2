import io
from functools import cached_property
from typing import Literal

from pydantic import BaseModel

from ..common.file import MemoryFile
from .base import BaseOutputDriver


class MemoryOutputConfig(BaseModel):
    engine: Literal["out:memory"]
    buffer_size: int = 1024

    @cached_property
    def driver(self) -> "MemoryOutput":
        return MemoryOutput(self)


class MemoryOutput(BaseOutputDriver):
    def __init__(self, config: MemoryOutputConfig):
        self.config = config

    required = ["buffer"]

    def __call__(
        self, file: MemoryFile, path: str = "", buffer: io.BytesIO | None = None
    ) -> None:
        """Write to a memory buffer."""
        if not buffer:
            raise ValueError("Buffer is required for memory output.")
        file.copy_into(buffer, self.config.buffer_size)
