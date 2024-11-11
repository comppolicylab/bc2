import re
from functools import cached_property, partial
from typing import Literal

from ..common.context import Context
from ..common.file import MemoryFile
from ..common.text import RedactedText, escape_for_txt
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

    def __call__(self, redaction: RedactedText, context: Context) -> MemoryFile:
        f = MemoryFile()

        if self.config.title:
            f.write(f"=== {self.config.title} ===")
            f.write("\n\n\n")

        # TODO: might want to add some formatting for the diff
        f.write(
            redaction.format(
                style=lambda x, _: x,
                p=lambda x: f"{x}\n\n",
                escape=partial(escape_for_txt, debug=context.debug),
            )
        )

        if self.config.disclaimer:
            f.write("\n")
            f.write("-------------------------------------------------------\n")
            # Strip HTML tags from the normal disclaimer
            f.write(re.sub(r"<[^>]*>", "", self.disclaimer()))

        return f
