import json
import logging
from functools import cached_property
from typing import Literal

from ..common.context import Context
from ..common.openai import (
    OpenAIChatConfig,
    OpenAIChatOutput,
    OpenAIChatPrompt,
    OpenAIChatPromptInline,
    OpenAIConfig,
)
from ..common.text import RedactedText
from ..common.types import IdToNameMap, NameToReplacementMap
from .base import BaseInspectDriver

logger = logging.getLogger(__name__)


NAME_TO_REPLACEMENT_PROMPT_TPL = """\
Generate a mapping of real entity name to placeholder text, \
given the following XML collection.

[PLACEHOLDERS] is a collection of entities that were redacted in a text \
and the placeholder text that was used for each entity.

Deduplicate the collection to produce a mapping from real entity to placeholder text.

Keep in mind that entities may have variations such as nicknames, abbreviations, \
or other forms of the same name. This means that multiple variations of a name \
may map to the same placeholder text. When you see different names that refer to \
the same entity, only create one entry in the final mapping.

Output the final mapping as a JSON object with the real entity name as the key \
and the placeholder text as the value.

Use [NARRATIVE] for additional context to determine which names refer \
to the same person.

Your response should be a simple JSON map, such as:

{{
    "John Smith": "Person 1",
    "Jane Doe": "Person 2",
    "Officer Lee": "Officer 1"
}}

Do not include any other text or formatting in the response. \
It must be a valid JSON object.\
"""


PLACEHOLDERS_PROMPT_TPL = """\
[PLACEHOLDERS]
{placeholders}

[NARRATIVE]
{narrative}\
"""


class OpenAIReplacementsInspectChatGeneratorConfig(OpenAIChatConfig):
    method: Literal["chat"] = "chat"
    model: str
    system: OpenAIChatPrompt = OpenAIChatPromptInline(
        prompt=NAME_TO_REPLACEMENT_PROMPT_TPL,
    )


class OpenAIReplacementsInspectConfig(OpenAIConfig):
    """Reconcile aliases with OpenAI config."""

    engine: Literal["inspect:replacements"]
    generator: OpenAIReplacementsInspectChatGeneratorConfig

    @cached_property
    def driver(self) -> "OpenAIReplacementsInspectDriver":
        return OpenAIReplacementsInspectDriver(self)


class OpenAIReplacementsInspectDriver(BaseInspectDriver):
    def __init__(self, config: OpenAIReplacementsInspectConfig):
        self.config = config
        self.client = config.client.init()

    required = ["placeholders"]

    def __call__(
        self,
        redacted: RedactedText,
        context: Context,
        subjects: IdToNameMap | None = None,
        placeholders: NameToReplacementMap | None = None,
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

        # Turn list of annotations into a map from name to replacement
        placeholders = placeholders or NameToReplacementMap()
        for a in context.annotations:
            if a["original"] not in placeholders:
                placeholders.set_replacement_text(a["original"], a["redacted"])

        # TODO --- accumulate over the course of the run
        # TODO --- rename things!
        context.placeholders = self.generate_with_retry(redacted.original, placeholders)

        if context.debug:
            print("INFERRED REPLACEMENTS", context.placeholders)
            logger.info(f"Inferred replacements: {context.placeholders}")

        return redacted

    def generate_with_retry(
        self,
        input: str,
        placeholders: NameToReplacementMap,
        retries: int = 3,
    ) -> NameToReplacementMap:
        """Generate text from the config and the user input, with retries.

        Args:
            input: The input text.
            placeholders: The map inferred by the redaction process.
            retries: The number of retries to attempt.

        Returns:
            The new subjects map.
        """
        last_error: Exception | None = None
        for i in range(retries):
            try:
                output = self.generate(input, placeholders)
                logger.debug(f"Generated placeholders: {output}")
                return output
            except Exception as e:
                logger.error(f"Error generating placeholders (attempt {i + 1}): {e}")
                last_error = e

        raise ValueError("Error generating placeholders.") from last_error

    def generate(
        self, narrative: str, placeholders: NameToReplacementMap
    ) -> NameToReplacementMap:
        """Generate text from the config and the user input.

        Args:
            narrative: The original text.
            placeholders: The placeholers map inferred by the redaction process.

        Returns:
            The new subjects map.
        """
        input = PLACEHOLDERS_PROMPT_TPL.format(
            placeholders=placeholders.to_xml(),
            narrative=narrative,
        )
        response = self.config.generator.invoke(self.client, input)

        print("GOT RESPONSE", response.content)

        return self.parse(response, placeholders)

    def parse(
        self,
        response: OpenAIChatOutput,
        placeholders: NameToReplacementMap,
    ) -> NameToReplacementMap:
        """Parse the response from the generator.

        The response should be a JSON object mapping names to placeholders.

        Args:
            response: The response from the generator.
            subjects: The map of ID to subject name.
            placeholders: The placeholders map inferred by the redaction process
                (for validation).

        Returns:
            The new subjects map.
        """
        try:
            # The most common failure is that the response is wrapped into
            # a markdown code block. We remove this if it is present.
            content = response.content
            if content.startswith("```json"):
                content = content[7:-3]
            data = json.loads(content)
            # TODO: Validate the JSON response matches the subjects maps
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            raise ValueError("Error parsing JSON response.") from e

        return NameToReplacementMap(data)
