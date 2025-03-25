from functools import cached_property
from typing import Literal

from ..common.context import Context
from ..common.openai import OpenAIChatConfig, OpenAIChatOutput, OpenAIConfig
from ..common.text import Text
from .base import BaseParseDriver


class OpenAIParseConfig(OpenAIConfig):
    """OpenAI Parse config."""

    engine: Literal["parse:openai"]
    generator: OpenAIChatConfig

    @cached_property
    def driver(self) -> "OpenAIParseDriver":
        return OpenAIParseDriver(self)


class OpenAIParseDriver(BaseParseDriver):
    def __init__(self, config: OpenAIParseConfig):
        self.config = config
        self.client = config.client.init()

    def __call__(self, text: Text, context: Context) -> Text:
        parsed = self.generate(text.text, debug=context.debug)
        return Text(parsed.content, truncated=parsed.is_truncated)

    def generate(self, input: str, debug: bool = False) -> OpenAIChatOutput:
        """Generate text from the config and the user input.

        This method only supports textual inputs.

        This method is supported for only chat generators.
        """
        return self.config.generator.invoke(self.client, input)
