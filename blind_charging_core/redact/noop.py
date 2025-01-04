from functools import cached_property
from typing import Literal

from ..common.context import Context
from ..common.text import RedactedText, Text
from ..common.types import NameMap
from .base import BaseRedactConfig, BaseRedactDriver


class NoOpRedactConfig(BaseRedactConfig):
    """No-op Redact config."""

    engine: Literal["redact:noop"]

    @cached_property
    def driver(self) -> "NoOpRedactDriver":
        return NoOpRedactDriver(self)


class NoOpRedactDriver(BaseRedactDriver):
    def __init__(self, config: NoOpRedactConfig):
        self.config = config

    def __call__(
        self, narrative: Text, context: Context, aliases: NameMap | None = None
    ) -> RedactedText:
        """Don't actually redact anything, just pass through."""
        return RedactedText(narrative.text, narrative.text, self.config.delimiters)
