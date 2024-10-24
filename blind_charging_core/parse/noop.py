from functools import cached_property
from typing import Literal

from pydantic import BaseModel

from ..common.text import Text
from .base import BaseParseDriver


class NoOpParseConfig(BaseModel):
    """No-op Parse config."""

    engine: Literal["parse:noop"]

    @cached_property
    def driver(self) -> "NoOpParseDriver":
        return NoOpParseDriver(self)


class NoOpParseDriver(BaseParseDriver):
    def __init__(self, config: NoOpParseConfig):
        self.config = config

    def __call__(self, text: Text) -> Text:
        """Don't actually parse anything, just pass through."""
        return Text(text.text)
