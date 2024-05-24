from functools import cached_property
from typing import Literal

from pydantic import BaseModel

from ..common.file import MemoryFile
from .base import BaseInputDriver


class FileInputConfig(BaseModel):
    engine: Literal["file"]
    buffer_size: int = 1024

    @cached_property
    def driver(self) -> "FileInput":
        return FileInput(self)


class FileInput(BaseInputDriver):
    def __init__(self, config: FileInputConfig):
        self.config = config

    required = ["input_path"]

    def __call__(self, input_path: str = "") -> MemoryFile:
        """Read from a file."""
        if not input_path:
            raise ValueError("Path is required for file input.")
        f = MemoryFile()
        with open(input_path, "rb") as file:
            while True:
                data = file.read(self.config.buffer_size)
                if not data:
                    break
                f.writeb(data)
        return f
