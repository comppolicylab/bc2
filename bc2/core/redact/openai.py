from functools import cached_property
from typing import Literal, Self

from pydantic import model_validator

from ..common.context import Context
from ..common.openai import (
    OpenAIChatConfig,
    OpenAIChatOutput,
    OpenAIConfig,
    OpenAIResolverConfig,
)
from ..common.text import RedactedText, Text
from ..common.types import NameToReplacementMap
from .base import BaseRedactConfig, BaseRedactDriver


class OpenAIRedactConfig(BaseRedactConfig, OpenAIConfig):
    """OpenAI Redact config."""

    engine: Literal["redact:openai"]
    generator: OpenAIChatConfig
    resolver: OpenAIResolverConfig | None = None

    @model_validator(mode="after")
    def _validate_resolver(self) -> Self:
        # Derive a resolver from the generator if it's not set
        if not self.resolver:
            generator_cfg = self.generator.model_dump()
            generator_cfg["extender"] = None
            generator_cfg["system"] = {"prompt_id": "resolver"}
            self.resolver = OpenAIResolverConfig(**generator_cfg)
        # Inject the delimiters into the resolver instance
        self.resolver.delimiters = self.delimiters
        return self

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
        redacted = self.generate(narrative.text, placeholders=placeholders)
        context.last_output_truncated = redacted.is_truncated
        context.placeholders = redacted.placeholders
        return RedactedText(redacted.content, narrative.text, self.config.delimiters)

    def generate(
        self, input: str, placeholders: NameToReplacementMap | None = None
    ) -> OpenAIChatOutput:
        """Generate text from the config and the user input.

        This method only supports textual inputs.

        This method is supported for only chat generators.
        """

        output = self.config.generator.invoke_extend_resolve(
            self.client, input, self.config.resolver, placeholders
        )

        return output
