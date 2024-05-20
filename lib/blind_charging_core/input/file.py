from typing import Literal

from pydantic import BaseModel

from ..common.file import MemoryFile
from .base import BaseInputDriver


class FileInputConfig(BaseModel):
    engine: Literal["file"]
    buffer_size: int = 1024


class FileInput(BaseInputDriver):
    def __init__(self, config: FileInputConfig):
        self.config = config

    def __call__(self, path: str = "") -> MemoryFile:
        """Read from a file."""
        f = MemoryFile()
        with open(path, "rb") as file:
            while True:
                data = file.read(self.config.buffer_size)
                if not data:
                    break
                f.writeb(data)
        return f
