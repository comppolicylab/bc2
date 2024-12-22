from functools import cached_property
from typing import Literal

from ..common.context import Context
from ..common.extend import extend
from ..common.openai import OpenAIChatConfig, OpenAICompletionConfig, OpenAIConfig, OpenAIResolverConfig
from ..common.text import RedactedText, Text
from ..common.types import NameMap
from .base import BaseRedactConfig, BaseRedactDriver


class OpenAIRedactConfig(BaseRedactConfig, OpenAIConfig):
    """OpenAI Redact config."""

    engine: Literal["redact:openai"]
    generator: OpenAIChatConfig | OpenAICompletionConfig
    resolver: OpenAIResolverConfig

    @cached_property
    def driver(self) -> "OpenAIRedactDriver":
        return OpenAIRedactDriver(self)


class OpenAIRedactDriver(BaseRedactDriver):
    def __init__(self, config: OpenAIRedactConfig):
        self.config = config
        self.client = config.client.init()

    def __call__(self, narrative: Text, context: Context,
                 preset_aliases: NameMap | None = None) -> RedactedText:
        if not narrative.text or narrative.text == "No narratives found.":
            raise ValueError("No narrative text in input.")
        redacted = self.generate(narrative.text, preset_aliases=preset_aliases)
        context.aliases = redacted.aliases
        return RedactedText(redacted.content, narrative.text, self.config.delimiters)

    def generate(self, input: str, preset_aliases: NameMap | None = None) -> str:
        """Generate text from the config and the user input.

        This method only supports textual inputs.

        This method is supported for either completion or chat generators.
        """

        if self.config.generator.extender:
            output = extend(self.client,
                            input,
                            self.config.generator,
                            preset_aliases,
                            self.config.delimiters,
                            self.config.resolver)
        else:
            output = self.config.generator.invoke(self.client, input, 
                                                  preset_aliases=preset_aliases)
            output.aliases = self.config.resolver.resolve(self.client, input, 
                                                          output.content, preset_aliases, 
                                                          self.config.delimiters)

        return output

