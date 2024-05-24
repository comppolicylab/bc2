from functools import cached_property
from typing import Literal

from pydantic import BaseModel

from ..common.file import MemoryFile
from .base import BaseOutputDriver


class FileOutputConfig(BaseModel):
    engine: Literal["out:file"]
    buffer_size: int = 1024

    @cached_property
    def driver(self) -> "FileOutput":
        return FileOutput(self)


class FileOutput(BaseOutputDriver):
    def __init__(self, config: FileOutputConfig):
        self.config = config

    required = ["path"]

    def __call__(self, file: MemoryFile, output_path: str = "") -> None:
        """Write to a file."""
        if not output_path:
            raise ValueError("Path is required for file output.")
        file.buffer.seek(0)
        with open(output_path, "wb") as f:
            while True:
                data = file.buffer.read(self.config.buffer_size)
                if not data:
                    break
                f.write(data)
