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


ALIASES_SYSTEM_TPL = """\
Generate a mapping of ID to placeholder, given the following two XML collections.
[COLLECTION#1] associates an ID with a real name, \
and [COLLECTION#2] associates a real name with a placeholder.

Join the collections to produce a mapping from ID to placeholder.

Output the final mapping as a JSON object with the ID as the key and the \
placeholder as the value.

Remember that the IDs in [COLLECTION#1] are unique and each refer to at most \
one individual in [COLLECTION#2].

Remember that the names are human names and might have variations \
(nicknames, abbreviations, etc.).
This means multiple variants of a name might map to the same placeholder, \
like "Officer Smith" and "Officer John Smith" mapping to the \
same placeholder "Officer 1".

Use [NARRATIVE] for additional context to determine which names refer \
to the same person.

Only return the final output in JSON, do not include any other text in the response.\
"""


ALIASES_PROMPT_TPL = """\
[COLLECTION#1]
{known_subjects}

[COLLECTION#2]
{inferred_replacements}

[NARRATIVE]
{narrative}\
"""


class OpenAIAliasesInspectChatGeneratorConfig(OpenAIChatConfig):
    method: Literal["chat"] = "chat"
    model: str
    system: OpenAIChatPrompt = OpenAIChatPromptInline(
        engine="string",
        prompt=ALIASES_SYSTEM_TPL,
    )


class OpenAIAliasesInspectConfig(OpenAIConfig):
    """Reconcile aliases with OpenAI config."""

    engine: Literal["inspect:aliases"]
    generator: OpenAIAliasesInspectChatGeneratorConfig

    @cached_property
    def driver(self) -> "OpenAIAliasesInspectDriver":
        return OpenAIAliasesInspectDriver(self)


class OpenAIAliasesInspectDriver(BaseInspectDriver):
    def __init__(self, config: OpenAIAliasesInspectConfig):
        self.config = config
        self.client = config.client.init()

    required = ["subjects"]

    def __call__(
        self,
        redacted: RedactedText,
        context: Context,
        subjects: IdToNameMap | None = None,
    ) -> RedactedText:
        if not subjects:
            raise ValueError("Aliases are required for alias reconciliation.")

        if context.annotations is None:
            raise ValueError("Annotations are required for alias reconciliation.")

        # Turn list of annotations into a map from name to alias
        placeholders = NameToReplacementMap()
        for a in context.annotations:
            placeholders.set_replacement_text(a["original"], a["redacted"])
        context.aliases = self.generate_with_retry(
            redacted.original, subjects, placeholders
        )
        return redacted

    def generate_with_retry(
        self,
        input: str,
        subjects: IdToNameMap,
        placeholders: NameToReplacementMap,
        retries: int = 3,
    ) -> NameToReplacementMap:
        """Generate text from the config and the user input, with retries.

        Args:
            input: The input text.
            subjects: The subjects identified by an ID.
            placeholders: The aliases map inferred by the redaction process.
            retries: The number of retries to attempt.

        Returns:
            The new aliases map.
        """
        last_error: Exception | None = None
        for i in range(retries):
            try:
                output = self.generate(input, subjects, placeholders)
                logger.debug(f"Generated aliases: {output}")
                return output
            except Exception as e:
                logger.error(f"Error generating aliases (attempt {i + 1}): {e}")
                last_error = e

        raise ValueError("Error generating aliases.") from last_error

    def generate(
        self, redacted: str, subjects: IdToNameMap, placeholders: NameToReplacementMap
    ) -> NameToReplacementMap:
        """Generate text from the config and the user input.

        Args:
            redacted: The redacted text.
            subjects: The subjects identified by an ID.
            placeholders: The placeholers map inferred by the redaction process.

        Returns:
            The new aliases map.
        """
        input = ALIASES_PROMPT_TPL.format(
            known_subjects=subjects.to_xml(),
            inferred_replacements=placeholders.to_xml(),
            narrative=redacted,
        )
        response = self.config.generator.invoke(self.client, input)
        return self.parse(response, subjects, placeholders)

    def parse(
        self,
        response: OpenAIChatOutput,
        subjects: IdToNameMap,
        placeholders: NameToReplacementMap,
    ) -> NameToReplacementMap:
        """Parse the response from the generator.

        The response should be a JSON object mapping IDs to aliases.

        Args:
            response: The response from the generator.
            subjects: The map of ID to subject name.
            placeholders: The placeholders map inferred by the redaction process
                (for validation).

        Returns:
            The new aliases map.
        """
        try:
            data = json.loads(response.content)
            # TODO: Validate the JSON response matches the alias maps
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            raise ValueError("Error parsing JSON response.") from e

        return data
