from functools import cached_property
from typing import Literal

from pydantic import BaseModel

from ..common.file import MemoryFile
from ..common.text import Text
from .base import BaseExtractDriver, register_preprocessor


class NoOpExtractConfig(BaseModel):
    engine: Literal["extract:noop"]

    @cached_property
    def driver(self) -> "NoOpExtractDriver":
        return NoOpExtractDriver(self)


class NoOpExtractDriver(BaseExtractDriver[str]):
    def __init__(self, config: NoOpExtractConfig) -> None:
        self.config = config

    def extract(self, text: Text) -> str:
        return text.text
    
    @register_preprocessor(r"^text/.*")
    def convert_text(self, file: MemoryFile) -> Text:
        return Text(file.content().decode())