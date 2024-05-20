from typing import Literal

from pydantic import BaseModel

from ..common.file import MemoryFile
from .base import BaseOutputDriver


class FileOutputConfig(BaseModel):
    engine: Literal["file"]
    buffer_size: int = 1024


class FileOutput(BaseOutputDriver):
    def __init__(self, config: FileOutputConfig):
        self.config = config

    def __call__(self, file: MemoryFile, path: str = "") -> None:
        """Write to a file."""
        file.buffer.seek(0)
        with open(path, "wb") as f:
            while True:
                data = file.buffer.read(self.config.buffer_size)
                if not data:
                    break
                f.write(data)
