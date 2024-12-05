from abc import ABC, abstractmethod
from typing import Sequence

from pydantic import BaseModel

from ..common.text import RedactedText, Text
from ..common.types import NameMap


class BaseRedactConfig(BaseModel):
    # The tokens that mark the beginning and end of a redaction.
    delimiters: Sequence[str] = ("[", "]")


class BaseRedactDriver(ABC):
    @abstractmethod
    def __call__(
        self, narrative: Text, aliases: NameMap | None = None
    ) -> RedactedText: ...
