from functools import cached_property
from typing import Literal

from ..common.context import Context
from ..common.extend import extend
from ..common.openai import OpenAIChatConfig, OpenAICompletionConfig, OpenAIConfig
from ..common.text import Text
from .base import BaseParseDriver


class OpenAIParseConfig(OpenAIConfig):
    """OpenAI Parse config."""

    engine: Literal["parse:openai"]
    generator: OpenAIChatConfig | OpenAICompletionConfig

    @cached_property
    def driver(self) -> "OpenAIParseDriver":
        return OpenAIParseDriver(self)


class OpenAIParseDriver(BaseParseDriver):
    def __init__(self, config: OpenAIParseConfig):
        self.config = config
        self.client = config.client.init()

    def __call__(self, text: Text, context: Context) -> Text:
        parsed = self.generate(text.text, debug=context.debug)
        return Text(parsed)

    def generate(self, input: str, debug: bool = False) -> str:
        """Generate text from the config and the user input.

        This method only supports textual inputs.

        This method is supported for either completion or chat generators.
        """
        if self.config.generator.extender:
            output = extend(self.client,
                            input,
                            self.config.generator,
                            debug=debug)
        else:
            output = self.config.generator.invoke(self.client, input)

        return output.content
