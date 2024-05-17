import sys
from typing import Literal

from pydantic import BaseModel

from ..common.file import MemoryFile
from .base import BaseOutputDriver


class StdoutOutputConfig(BaseModel):
    engine: Literal["stdout"]
    buffer_size: int = 1024


class StdoutOutput(BaseOutputDriver):
    def __init__(self, config: StdoutOutputConfig):
        self.config = config

    def __call__(self, file: MemoryFile, path: str = "") -> None:
        """Write to stdout."""
        file.buffer.seek(0)
        while True:
            b = file.buffer.read(self.config.buffer_size)
            if not b:
                break
            sys.stdout.buffer.write(b)
