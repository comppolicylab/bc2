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
from ..common.types import IdToMaskMap, IdToNameMap, NameToMaskMap
from .base import BaseInspectDriver

logger = logging.getLogger(__name__)


DATA_PROMPT_TPL = """\
[COLLECTION#1]
{known_subjects}

[COLLECTION#2]
{inferred_replacements}

[NARRATIVE]
{narrative}\
"""


class OpenAIMaskedSubjectsInspectChatGeneratorConfig(OpenAIChatConfig):
    method: Literal["chat"] = "chat"
    model: str
    system: OpenAIChatPrompt = OpenAIChatPromptBuiltIn(
        prompt_id="subject_masks",
    )


class OpenAIMaskedSubjectsInspectConfig(OpenAIConfig):
    """Reconcile aliases with OpenAI config."""

    engine: Literal["inspect:subject_masks"] = "inspect:subject_masks"
    generator: OpenAIMaskedSubjectsInspectChatGeneratorConfig

    @cached_property
    def driver(self) -> "OpenAIMaskedSubjectsInspectDriver":
        return OpenAIMaskedSubjectsInspectDriver(self)


class OpenAIMaskedSubjectsInspectDriver(BaseInspectDriver):
    def __init__(self, config: OpenAIMaskedSubjectsInspectConfig):
        self.config = config
        self.client = config.client.init()

    required = ["subjects"]

    def __call__(
        self,
        redacted: RedactedText,
        context: Context,
        subjects: IdToNameMap | None = None,
        placeholders: NameToMaskMap | None = None,
    ) -> RedactedText:
        if not subjects:
            logger.warning(
                "No subjects provided for id-mask reconciliation! "
                "Skipping this step."
            )
            return redacted

        if context.annotations is None:
            raise ValueError(
                "Annotations are required for id-mask reconciliation. "
                "This is a config error -- please run `inspect:annotations` "
                "before running this step."
            )

        # Turn list of annotations into a map from name to replacement
        placeholders = NameToMaskMap()
        for a in context.annotations:
            placeholders.set_mask(a["original"], a["redacted"])

        context.masked_subjects = self.generate_with_retry(
            redacted.original, subjects, placeholders, debug=context.debug
        )

        if context.debug:
            logger.info(f"Inferred subjects: {context.subjects}")

        return redacted

    def generate_with_retry(
        self,
        input: str,
        subjects: IdToNameMap,
        placeholders: NameToMaskMap,
        retries: int = 3,
        debug: bool = False,
    ) -> IdToMaskMap:
        """Generate text from the config and the user input, with retries.

        Args:
            input: The input text.
            subjects: The subjects identified by an ID.
            placeholders: The subjects map inferred by the redaction process.
            retries: The number of retries to attempt.

        Returns:
            The new masked subjects map.
        """
        last_error: Exception | None = None
        for i in range(retries):
            try:
                output = self.generate(input, subjects, placeholders, debug=debug)
                logger.debug(f"Generated subjects: {output}")
                return output
            except Exception as e:
                logger.error(f"Error generating subjects (attempt {i + 1}): {e}")
                last_error = e

        raise ValueError("Error generating subjects.") from last_error

    def generate(
        self,
        input: str,
        subjects: IdToNameMap,
        placeholders: NameToMaskMap,
        debug: bool = False,
    ) -> IdToMaskMap:
        """Generate text from the config and the user input.

        Args:
            input: The redacted text.
            subjects: The subjects identified by an ID.
            placeholders: The placeholers map inferred by the redaction process.

        Returns:
            The new masked subjects map.
        """
        input = DATA_PROMPT_TPL.format(
            known_subjects=subjects.to_xml(),
            inferred_replacements=placeholders.to_xml(),
            narrative=input,
        )
        response = self.config.generator.invoke(self.client, input)
        return self.parse(response, subjects, placeholders, debug=debug)

    def parse(
        self,
        response: OpenAIChatOutput,
        subjects: IdToNameMap,
        placeholders: NameToMaskMap,
        debug: bool = False,
    ) -> IdToMaskMap:
        """Parse the response from the generator.

        The response should be a JSON object mapping IDs to names.

        Args:
            response: The response from the generator.
            subjects: The map of ID to subject name.
            placeholders: The placeholders map inferred by the redaction process
                (for validation).

        Returns:
            The new masked subjects map.
        """
        data = parse_llm_json(response.content, debug=debug)

        return IdToMaskMap(data)
