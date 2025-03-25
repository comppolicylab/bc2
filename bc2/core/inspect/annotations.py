from functools import cached_property
from typing import Literal

from pydantic import BaseModel

from ..common.context import Context
from ..common.infer import infer_annotations
from ..common.name_map import IdToNameMap, NameToMaskMap
from ..common.text import RedactedText
from .base import BaseInspectDriver


class AnnotationsInspectConfig(BaseModel):
    """Configuration for the annotations inspect driver."""

    engine: Literal["inspect:annotations"] = "inspect:annotations"

    @cached_property
    def driver(self) -> "AnnotationsInspectDriver":
        """Return the annotations inspect driver."""
        return AnnotationsInspectDriver()


class AnnotationsInspectDriver(BaseInspectDriver):
    """Infer annotations in redacted text and store them in the context."""

    def __call__(
        self,
        input: RedactedText,
        context: Context,
        subjects: IdToNameMap | None = None,
        placeholders: NameToMaskMap | None = None,
    ) -> RedactedText:
        """Infer annotations in redacted text and store them in the context.

        Args:
            input: The redacted text.
            context: The context object.
            subjects: The subjects identified by an ID.
            placeholders: The subjects map inferred by the redaction process.

        Returns:
            The redacted text.
        """
        context.annotations = list(
            infer_annotations(
                input.original,
                input.redacted,
                delimiters=input.delimiters,
                truncated=input.truncated,
            )
        )
        return input
