from functools import cached_property
from typing import Literal

from pydantic import Field

from ..common.context import Context
from ..common.openai import (
    OpenAIChatConfig,
    OpenAIChatOutput,
    OpenAIConfig,
    OpenAIResolverConfig,
)
from ..common.text import RedactedText, Text
from ..common.types import NameMap
from .base import BaseRedactConfig, BaseRedactDriver


def _default_resolver(data: dict) -> OpenAIResolverConfig:
    """Create the default resolver.

    By default the resolver can essentially be the same as the generator.
    """
    generator_config = data.pop("generator", {})
    generator_config["extender"] = None
    generator_config["system"] = {"prompt_id": "resolver"}
    return OpenAIResolverConfig(**generator_config)


class OpenAIRedactConfig(BaseRedactConfig, OpenAIConfig):
    """OpenAI Redact config."""

    engine: Literal["redact:openai"]
    generator: OpenAIChatConfig
    resolver: OpenAIResolverConfig = Field(default_factory=_default_resolver)

    @cached_property
    def driver(self) -> "OpenAIRedactDriver":
        # Inject the delimiters into the resolver instance
        self.resolver.delimiters = self.delimiters
        return OpenAIRedactDriver(self)


class OpenAIRedactDriver(BaseRedactDriver):
    def __init__(self, config: OpenAIRedactConfig):
        self.config = config
        self.client = config.client.init()

    def __call__(
        self, narrative: Text, context: Context, aliases: NameMap | None = None
    ) -> RedactedText:
        if not narrative.text or narrative.text == "No narratives found.":
            raise ValueError("No narrative text in input.")
        redacted = self.generate(narrative.text, aliases=aliases)
        # To do: Change the context prop to whatever name we decide makes sense
        context.aliases = redacted.aliases
        return RedactedText(redacted.content, narrative.text, self.config.delimiters)

    def generate(self, input: str, aliases: NameMap | None = None) -> OpenAIChatOutput:
        """Generate text from the config and the user input.

        This method only supports textual inputs.

        This method is supported for only chat generators.
        """

        output = self.config.generator.invoke_extend_resolve(
            self.client, input, self.config.resolver, aliases
        )

        return output
