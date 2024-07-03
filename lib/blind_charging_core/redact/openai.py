from functools import cached_property
from typing import Literal

from ..common.openai import OpenAIChatConfig, OpenAICompletionConfig, OpenAIConfig
from ..common.text import RedactedText, Text
from .base import AliasMap, BaseRedactConfig, BaseRedactDriver


class OpenAIRedactConfig(BaseRedactConfig, OpenAIConfig):
    """OpenAI Redact config."""

    engine: Literal["redact:openai"]
    generator: OpenAIChatConfig | OpenAICompletionConfig

    @cached_property
    def driver(self) -> "OpenAIRedactDriver":
        return OpenAIRedactDriver(self)


class OpenAIRedactDriver(BaseRedactDriver):
    def __init__(self, config: OpenAIRedactConfig):
        self.config = config
        self.client = config.client.init()

    def __call__(
        self, narrative: Text, aliases: AliasMap | None = None
    ) -> RedactedText:
        redacted = self.generate(narrative.text, aliases=aliases)
        return RedactedText(redacted, narrative.text, self.config.delimiters)

    def generate(self, input: str, aliases: AliasMap | None = None) -> str:
        """Generate text from the config and the user input.

        This method only supports textual inputs.

        This method is supported for either completion or chat generators.
        """
        return self.config.generator.invoke(self.client, input, aliases=aliases)
