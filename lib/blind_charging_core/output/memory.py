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

    def __call__(self, file: MemoryFile, path: str = "") -> io.BytesIO | None:
        """Write to a memory buffer."""
        output = io.BytesIO()
        file.buffer.seek(0)
        while True:
            b = file.buffer.read(self.config.buffer_size)
            if not b:
                break
            output.write(b)
        return output
