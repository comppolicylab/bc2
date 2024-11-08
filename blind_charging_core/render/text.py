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
    ancillary_content: bool = True

    @cached_property
    def driver(self) -> "TextRenderer":
        return TextRenderer(self)


class TextRenderer(BaseRenderer):
    def __init__(self, config: TextRenderConfig) -> None:
        self.config = config

    def __call__(self, redaction: RedactedText, context: Context) -> MemoryFile:
        f = MemoryFile()

        if self.config.ancillary_content:
            f.write(self.TITLE)
            f.write("\n\n\n")
            f.write("=== NARRATIVE ===\n")

        # TODO: might want to add some formatting for the diff
        f.write(
            redaction.format(
                style=lambda x, _: x,
                p=lambda x: f"{x}\n\n",
                escape=partial(escape_for_txt, debug=context.debug),
            )
        )

        if self.config.ancillary_content:
            f.write("---------------------------------------------------------")
            # Strip HTML tags from the normal disclaimer
            f.write(re.sub(r"<[^>]*>", "", self.disclaimer()))
            f.write("\n\n")
            f.write("=== END OF DOCUMENT ===\n")

        return f
