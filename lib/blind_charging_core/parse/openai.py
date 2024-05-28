from functools import cached_property
from typing import Literal

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

    def __call__(self, narrative: Text) -> Text:
        parsed = self.generate(narrative.text)
        return Text(parsed)

    def generate(self, input: str) -> str:
        """Generate text from the config and the user input.

        This method only supports textual inputs.

        This method is supported for either completion or chat generators.
        """
        return self.config.generator.invoke(self.client, input)
