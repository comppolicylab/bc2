from abc import ABC, abstractmethod
from typing import Sequence

from pydantic import BaseModel

from ..common.context import Context
from ..common.name_map import NameToMaskMap
from ..common.text import RedactedText, Text


class MissingNarrativeError(Exception):
    """Error when narrative text is not present in input."""

    pass


class BaseRedactConfig(BaseModel):
    # The tokens that mark the beginning and end of a redaction.
    delimiters: Sequence[str] = ("[", "]")


class BaseRedactDriver(ABC):
    @abstractmethod
    def __call__(
        self,
        narrative: Text,
        context: Context,
        placeholders: NameToMaskMap | None = None,
    ) -> RedactedText: ...
