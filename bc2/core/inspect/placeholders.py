import logging
from functools import cached_property
from typing import Literal

from ..common.context import Context
from ..common.json import parse_llm_json
from ..common.openai import (
    OpenAIChatConfig,
    OpenAIChatOutput,
    OpenAIChatPrompt,
    OpenAIChatPromptBuiltIn,
    OpenAIConfig,
)
from ..common.text import RedactedText
from ..common.types import IdToNameMap, NameToMaskMap
from .base import BaseInspectDriver

logger = logging.getLogger(__name__)


PLACEHOLDERS_PROMPT_TPL = """\
[PLACEHOLDERS]
{placeholders}

[NARRATIVE]
{narrative}\
"""


class OpenAIPlaceholdersInspectChatGeneratorConfig(OpenAIChatConfig):
    method: Literal["chat"] = "chat"
    model: str
    system: OpenAIChatPrompt = OpenAIChatPromptBuiltIn(
        prompt_id="placeholders",
    )


class OpenAIPlaceholdersInspectConfig(OpenAIConfig):
    """Reconcile aliases with OpenAI config."""

    engine: Literal["inspect:placeholders"] = "inspect:placeholders"
    generator: OpenAIPlaceholdersInspectChatGeneratorConfig

    @cached_property
    def driver(self) -> "OpenAIPlaceholdersInspectDriver":
        return OpenAIPlaceholdersInspectDriver(self)


class OpenAIPlaceholdersInspectDriver(BaseInspectDriver):
    def __init__(self, config: OpenAIPlaceholdersInspectConfig):
        self.config = config
        self.client = config.client.init()

    required = ["placeholders"]

    def __call__(
        self,
        redacted: RedactedText,
        context: Context,
        subjects: IdToNameMap | None = None,
        placeholders: NameToMaskMap | None = None,
    ) -> RedactedText:
        if not placeholders:
            # Not a critical error, might be a mistake / bug.
            logger.debug("No existing placeholders provided for reconciliation!")

        if context.annotations is None:
            raise ValueError(
                "Annotations are required for placeholder reconciliation. "
                "This is a config error -- please run `inspect:annotations` "
                "before running this step."
            )

        # Turn list of annotations into a map from name to mask
        placeholders = NameToMaskMap.merge(placeholders, context.placeholders)
        for a in context.annotations:
            if a["original"] not in placeholders:
                placeholders.set_mask(a["original"], a["redacted"])

        context.placeholders = self.generate_with_retry(
            redacted.original, placeholders, debug=context.debug
        )

        if context.debug:
            logger.info(f"Generated placeholders: {context.placeholders.to_json()}")

        return redacted

    def generate_with_retry(
        self,
        input: str,
        placeholders: NameToMaskMap,
        retries: int = 3,
        debug: bool = False,
    ) -> NameToMaskMap:
        """Generate text from the config and the user input, with retries.

        Args:
            input: The input text.
            placeholders: The map inferred by the redaction process.
            retries: The number of retries to attempt.

        Returns:
            The new placeholders map.
        """
        last_error: Exception | None = None
        for i in range(retries):
            try:
                output = self.generate(input, placeholders, debug=debug)
                logger.debug(f"Generated placeholders: {output}")
                return output
            except Exception as e:
                logger.error(f"Error generating placeholders (attempt {i + 1}): {e}")
                last_error = e

        raise ValueError("Error generating placeholders.") from last_error

    def generate(
        self,
        narrative: str,
        placeholders: NameToMaskMap,
        debug: bool = False,
    ) -> NameToMaskMap:
        """Generate text from the config and the user input.

        Args:
            narrative: The original text.
            placeholders: The placeholers map inferred by the redaction process.

        Returns:
            The new placeholders map.
        """
        input = PLACEHOLDERS_PROMPT_TPL.format(
            placeholders=placeholders.to_xml(),
            narrative=narrative,
        )
        response = self.config.generator.invoke(self.client, input)

        return self.parse(response, placeholders, debug=debug)

    def parse(
        self,
        response: OpenAIChatOutput,
        placeholders: NameToMaskMap,
        debug: bool = False,
    ) -> NameToMaskMap:
        """Parse the response from the generator.

        The response should be a JSON object mapping names to placeholders.

        Args:
            response: The response from the generator.
            placeholders: The placeholders map inferred by the redaction process
                (for validation).

        Returns:
            The new placeholders map.
        """
        data = parse_llm_json(response.content, debug=debug)

        return NameToMaskMap(data)
