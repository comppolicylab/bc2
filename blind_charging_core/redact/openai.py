from functools import cached_property
from typing import Literal

from ..common.context import Context
from ..common.openai import (OpenAIChatOutput,
                             OpenAIChatConfig, 
                             OpenAIConfig, 
                             OpenAIResolverConfig)
from ..common.text import RedactedText, Text
from ..common.types import NameMap
from .base import BaseRedactConfig, BaseRedactDriver


class OpenAIRedactConfig(BaseRedactConfig, OpenAIConfig):
    """OpenAI Redact config."""

    engine: Literal["redact:openai"]
    generator: OpenAIChatConfig
    resolver: OpenAIResolverConfig

    @cached_property
    def driver(self) -> "OpenAIRedactDriver":
        return OpenAIRedactDriver(self)


class OpenAIRedactDriver(BaseRedactDriver):
    def __init__(self, config: OpenAIRedactConfig):
        self.config = config
        self.client = config.client.init()

    def __call__(self, narrative: Text, context: Context,
                 aliases: NameMap | None = None) -> RedactedText:
        if not narrative.text or narrative.text == "No narratives found.":
            raise ValueError("No narrative text in input.")
        redacted = self.generate(narrative.text, aliases=aliases)
        # To do: Change the context prop to whatever name we decide makes sense
        context.aliases = redacted.aliases
        return RedactedText(redacted.content, narrative.text, self.config.delimiters)

    def generate(self, input: str, 
                 aliases: NameMap | None = None) -> OpenAIChatOutput:
        """Generate text from the config and the user input.

        This method only supports textual inputs.

        This method is supported for only chat generators.
        """

        output = self.config.generator.invoke_extend_resolve(
            self.client, 
            input, 
            self.config.resolver,
            self.config.delimiters,
            aliases
        )

        return output

