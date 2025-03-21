from functools import cached_property
from typing import Literal

from pydantic import Field

from ..common.context import Context
from ..common.openai import (
    OpenAIChatConfig,
    OpenAIChatOutput,
    OpenAIConfig,
)
from ..common.text import RedactedText, Text
from ..common.types import NameToReplacementMap
from .base import BaseRedactConfig, BaseRedactDriver


class OpenAIRedactConfig(BaseRedactConfig, OpenAIConfig):
    """OpenAI Redact config."""

    engine: Literal["redact:openai"]
    generator: OpenAIChatConfig
    resolver: None = Field(
        None,
        description="Deprecated! use chunk+inspect instead.",
    )

    @cached_property
    def driver(self) -> "OpenAIRedactDriver":
        return OpenAIRedactDriver(self)


class OpenAIRedactDriver(BaseRedactDriver):
    def __init__(self, config: OpenAIRedactConfig):
        self.config = config
        self.client = config.client.init()

    def __call__(
        self,
        narrative: Text,
        context: Context,
        placeholders: NameToReplacementMap | None = None,
    ) -> RedactedText:
        if not narrative.text or narrative.text == "No narratives found.":
            raise ValueError("No narrative text in input.")

        placeholders = NameToReplacementMap.merge(placeholders, context.placeholders)
        redacted = self.generate(narrative.text, placeholders=placeholders)
        return RedactedText(
            redacted.content,
            narrative.text,
            delimiters=self.config.delimiters,
            truncated=redacted.is_truncated,
        )

    def generate(
        self, input: str, placeholders: NameToReplacementMap | None = None
    ) -> OpenAIChatOutput:
        """Generate text from the config and the user input.

        This method only supports textual inputs.

        This method is supported for only chat generators.
        """
        xml = placeholders.to_xml() if placeholders else "<Names><!-- empty --></Names>"
        output = self.config.generator.invoke(
            self.client,
            input,
            placeholders=xml,
        )

        return output
