import io
import sys
from functools import cached_property
from typing import Literal

from pydantic import BaseModel

from ..common.file import MemoryFile
from .base import BaseInputDriver


class StdinInputConfig(BaseModel):
    engine: Literal["in:stdin"]
    buffer_size: int = 1024

    @cached_property
    def driver(self) -> "StdinInput":
        return StdinInput(self)


class StdinInput(BaseInputDriver):
    def __init__(self, config: StdinInputConfig):
        self.config = config

    def load_file(
        self,
        path: str = "",
        buffer: io.BytesIO | None = None,
        mime_type: str | None = None,
    ) -> MemoryFile:
        """Read from stdin."""
        f = MemoryFile(mime_type=mime_type)
        # Consume all the stdin pipe and write it to memory
        while True:
            data = sys.stdin.buffer.read(self.config.buffer_size)
            if not data:
                break
            f.writeb(data)
        return f
