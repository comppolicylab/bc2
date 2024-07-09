from abc import ABC, abstractmethod
from typing import Sequence

from pydantic import BaseModel

from ..common.text import RedactedText, Text


class BaseRedactConfig(BaseModel):
    # The tokens that mark the beginning and end of a redaction.
    delimiters: Sequence[str] = ("<", ">")


AliasMap = dict[str, str]
"""A mapping of human names to aliases.

Example:
{
    "Leopold Nudell": "Accused 1",
}
"""


class BaseRedactDriver(ABC):
    @abstractmethod
    def __call__(
        self, narrative: Text, aliases: AliasMap | None = None
    ) -> RedactedText: ...
