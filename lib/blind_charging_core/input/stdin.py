import sys
from functools import cached_property
from typing import Literal

from pydantic import BaseModel

from ..common.file import MemoryFile
from .base import BaseInputDriver


class StdinInputConfig(BaseModel):
    engine: Literal["stdin"]
    buffer_size: int = 1024

    @cached_property
    def driver(self) -> "StdinInput":
        return StdinInput(self)


class StdinInput(BaseInputDriver):
    def __init__(self, config: StdinInputConfig):
        self.config = config

    def __call__(self, input_path: str = "") -> MemoryFile:
        """Read from stdin."""
        f = MemoryFile()
        # Consume all the stdin pipe and write it to memory
        while True:
            data = sys.stdin.buffer.read(self.config.buffer_size)
            if not data:
                break
            f.writeb(data)
        return f
