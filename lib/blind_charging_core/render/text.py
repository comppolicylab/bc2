import re
from functools import cached_property
from typing import Literal

from ..common.file import MemoryFile
from ..common.text import RedactedText
from .base import BaseRenderConfig, BaseRenderer


class TextRenderConfig(BaseRenderConfig):
    """Text Render config."""

    engine: Literal["render:text"]

    @cached_property
    def driver(self) -> "TextRenderer":
        return TextRenderer(self)


class TextRenderer(BaseRenderer):
    def __init__(self, config: TextRenderConfig) -> None:
        self.config = config

    def __call__(self, redaction: RedactedText) -> MemoryFile:
        f = MemoryFile()
        f.write(self.TITLE)
        f.write("\n\n")
        # Strip HTML tags from the normal disclaimer
        f.write(re.sub(r"<[^>]*>", "", self.DISCLAIMER))
        f.write("\n\n")
        f.write("=== NARRATIVE ===\n")
        # TODO: might want to add some formatting for the diff
        f.write(
            redaction.format(
                style=lambda x, y: x,
                p=lambda x: f"{x}\n\n",
                escape=lambda x: x,
            )
        )
        f.write("=== END OF DOCUMENT ===\n")
        return f
