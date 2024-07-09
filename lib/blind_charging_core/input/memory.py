import io
from functools import cached_property
from typing import Literal

from pydantic import BaseModel

from ..common.file import MemoryFile
from .base import BaseInputDriver


class MemoryInputConfig(BaseModel):
    engine: Literal["in:memory"]
    buffer_size: int = 1024

    @cached_property
    def driver(self) -> "MemoryInput":
        return MemoryInput(self)


class MemoryInput(BaseInputDriver):
    def __init__(self, config: MemoryInputConfig):
        self.config = config

    required = ["buffer"]

    def __call__(self, path: str = "", buffer: io.BytesIO | None = None) -> MemoryFile:
        """Read from a buffer in memory."""
        if not buffer:
            raise ValueError("Buffer is required for memory input.")
        f = MemoryFile()
        # Consume all the buffer and write it to memory
        while True:
            data = buffer.read(self.config.buffer_size)
            if not data:
                break
            f.writeb(data)
        return f
