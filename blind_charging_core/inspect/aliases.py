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
from ..common.types import NameMap
from .base import BaseInspectDriver

logger = logging.getLogger(__name__)


ALIASES_SYSTEM_TPL = """\
Generate a mapping of ID to alias, given the following two maps.
[MAP#1] associates an ID with a name, and [MAP#2] associates a name with an alias.

Join the maps based on the names to create a map of ID to alias.

Output the final mapping as a JSON object with the ID as the key and the \
alias as the value.

Remember that the IDs in [MAP#1] are unique and each refer to at most \
one individual in [MAP#2].

Remember that the names are human names and might have variations \
(nicknames, abbreviations, etc.).
This means multiple variants of a name might map to the same alias, \
like "Officer Smith" and "Officer John Smith" mapping to the same alias "Officer 1".

Use [NARRATIVE] for additional context to determine which names refer \
to the same person.

Only return the final output in JSON, do not include any other text in the response.\
"""


ALIASES_PROMPT_TPL = """\
[MAP#1]
{preset_aliases}

[MAP#2]
{inferred_aliases}

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

    required = ["aliases"]

    def __call__(
        self,
        redacted: RedactedText,
        context: Context,
        aliases: NameMap | None = None,
    ) -> RedactedText:
        if not aliases:
            raise ValueError("Aliases are required for alias reconciliation.")

        if context.annotations is None:
            raise ValueError("Annotations are required for alias reconciliation.")

        # Turn list of annotations into a map from name to alias
        inferred_aliases = {a["original"]: a["redacted"] for a in context.annotations}
        context.aliases = self.generate_with_retry(
            redacted.original, aliases, inferred_aliases
        )
        return redacted

    def generate_with_retry(
        self,
        input: str,
        preset_aliases: NameMap,
        inferred_aliases: NameMap,
        retries: int = 3,
    ) -> NameMap:
        """Generate text from the config and the user input, with retries.

        Args:
            input: The input text.
            preset_aliases: The preexisting aliases map.
            inferred_aliases: The aliases map inferred by the redaction process.
            retries: The number of retries to attempt.

        Returns:
            The new aliases map.
        """
        last_error: Exception | None = None
        for i in range(retries):
            try:
                output = self.generate(input, preset_aliases, inferred_aliases)
                logger.debug(f"Generated aliases: {output}")
                return output
            except Exception as e:
                logger.error(f"Error generating aliases (attempt {i + 1}): {e}")
                last_error = e

        raise ValueError("Error generating aliases.") from last_error

    def generate(
        self, redacted: str, preset_aliases: NameMap, inferred_aliases: NameMap
    ) -> NameMap:
        """Generate text from the config and the user input.

        Args:
            redacted: The redacted text.
            preset_aliases: The preexisting aliases map.
            inferred_aliases: The aliases map inferred by the redaction process.

        Returns:
            The new aliases map.
        """
        input = ALIASES_PROMPT_TPL.format(
            preset_aliases=json.dumps(preset_aliases, indent=2, sort_keys=True),
            inferred_aliases=json.dumps(inferred_aliases, indent=2, sort_keys=True),
            narrative=redacted,
        )
        response = self.config.generator.invoke(self.client, input)
        return self.parse(response, preset_aliases, inferred_aliases)

    def parse(
        self,
        response: OpenAIChatOutput,
        preset_aliases: NameMap,
        inferred_aliases: NameMap,
    ) -> NameMap:
        """Parse the response from the generator.

        The response should be a JSON object mapping IDs to aliases.

        Args:
            response: The response from the generator.
            preset_aliases: The preexisting aliases map (for validation).
            inferred_aliases: The aliases map inferred by the redaction process
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
