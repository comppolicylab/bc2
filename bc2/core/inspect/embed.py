from functools import cached_property
from typing import Literal

from ...lib.embedding.openai import OpenAIEmbeddingConfig, OpenAIEmbeddingDriver
from ..common.context import Context
from ..common.name_map import IdToNameMap, NameToMaskMap
from ..common.text import RedactedText
from .base import BaseInspectDriver


class EmbedInspectConfig(OpenAIEmbeddingConfig):
    """Configuration for the embedding inspect driver."""

    engine: Literal["inspect:embed"] = "inspect:embed"

    @cached_property
    def driver(self) -> "EmbedInspectDriver":
        """Return the annotations inspect driver."""
        client = self.client.init()
        aclient = self.client.init_async()
        return EmbedInspectDriver(client, aclient, self.generator)


class EmbedInspectDriver(OpenAIEmbeddingDriver, BaseInspectDriver):
    """Generate an embedding for the redacted text and store it in the context."""

    def __call__(
        self,
        input: RedactedText,
        context: Context,
        subjects: IdToNameMap | None = None,
        placeholders: NameToMaskMap | None = None,
    ) -> RedactedText:
        """Generate embedding in redacted text and store them in the context.

        Args:
            input: The redacted text.
            context: The context object.
            subjects: The subjects identified by an ID.
            placeholders: The subjects map inferred by the redaction process.

        Returns:
            The redacted text.
        """
        context.embedding = self.embed(input.redacted)
        return input
