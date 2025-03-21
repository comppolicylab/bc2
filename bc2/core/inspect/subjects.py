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


ID_TO_NAME_PROMPT_TPL = """\
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


DATA_PROMPT_TPL = """\
[COLLECTION#1]
{known_subjects}

[COLLECTION#2]
{inferred_replacements}

[NARRATIVE]
{narrative}\
"""


class OpenAISubjectsInspectChatGeneratorConfig(OpenAIChatConfig):
    method: Literal["chat"] = "chat"
    model: str
    system: OpenAIChatPrompt = OpenAIChatPromptInline(
        prompt=ID_TO_NAME_PROMPT_TPL,
    )


class OpenAISubjectsInspectConfig(OpenAIConfig):
    """Reconcile aliases with OpenAI config."""

    engine: Literal["inspect:subjects"]
    generator: OpenAISubjectsInspectChatGeneratorConfig

    @cached_property
    def driver(self) -> "OpenAISubjectsInspectDriver":
        return OpenAISubjectsInspectDriver(self)


class OpenAISubjectsInspectDriver(BaseInspectDriver):
    def __init__(self, config: OpenAISubjectsInspectConfig):
        self.config = config
        self.client = config.client.init()

    required = ["subjects"]

    def __call__(
        self,
        redacted: RedactedText,
        context: Context,
        subjects: IdToNameMap | None = None,
        placeholders: NameToReplacementMap | None = None,
    ) -> RedactedText:
        if not subjects:
            logger.warning(
                "No subjects provided for id-name reconciliation! "
                "Skipping this step."
            )
            return redacted

        if context.annotations is None:
            raise ValueError(
                "Annotations are required for id-name reconciliation. "
                "This is a config error -- please run `inspect:annotations` "
                "before running this step."
            )

        # Turn list of annotations into a map from name to replacement
        placeholders = NameToReplacementMap()
        for a in context.annotations:
            placeholders.set_replacement_text(a["original"], a["redacted"])

        # TODO --- accumulate over the course of the run
        # TODO --- rename things!
        context.subjects = self.generate_with_retry(
            redacted.original, subjects, placeholders
        )

        if context.debug:
            logger.info(f"Inferred subjects: {context.subjects}")

        return redacted

    def generate_with_retry(
        self,
        input: str,
        subjects: IdToNameMap,
        placeholders: NameToReplacementMap,
        retries: int = 3,
    ) -> IdToNameMap:
        """Generate text from the config and the user input, with retries.

        Args:
            input: The input text.
            subjects: The subjects identified by an ID.
            placeholders: The subjects map inferred by the redaction process.
            retries: The number of retries to attempt.

        Returns:
            The new subjects map.
        """
        last_error: Exception | None = None
        for i in range(retries):
            try:
                output = self.generate(input, subjects, placeholders)
                logger.debug(f"Generated subjects: {output}")
                return output
            except Exception as e:
                logger.error(f"Error generating subjects (attempt {i + 1}): {e}")
                last_error = e

        raise ValueError("Error generating subjects.") from last_error

    def generate(
        self, input: str, subjects: IdToNameMap, placeholders: NameToReplacementMap
    ) -> IdToNameMap:
        """Generate text from the config and the user input.

        Args:
            input: The redacted text.
            subjects: The subjects identified by an ID.
            placeholders: The placeholers map inferred by the redaction process.

        Returns:
            The new subjects map.
        """
        input = DATA_PROMPT_TPL.format(
            known_subjects=subjects.to_xml(),
            inferred_replacements=placeholders.to_xml(),
            narrative=input,
        )
        response = self.config.generator.invoke(self.client, input)
        return self.parse(response, subjects, placeholders)

    def parse(
        self,
        response: OpenAIChatOutput,
        subjects: IdToNameMap,
        placeholders: NameToReplacementMap,
    ) -> IdToNameMap:
        """Parse the response from the generator.

        The response should be a JSON object mapping IDs to names.

        Args:
            response: The response from the generator.
            subjects: The map of ID to subject name.
            placeholders: The placeholders map inferred by the redaction process
                (for validation).

        Returns:
            The new subjects map.
        """
        try:
            data = json.loads(response.content)
            # TODO: Validate the JSON response matches the subjects maps
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            raise ValueError("Error parsing JSON response.") from e

        return IdToNameMap(data)
