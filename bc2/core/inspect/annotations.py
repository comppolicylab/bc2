import logging
from functools import cached_property
from typing import Literal

from pydantic import BaseModel

from ..common.context import Context
from ..common.infer import infer_annotations, remove_hanging_redactions
from ..common.name_map import IdToNameMap, NameToMaskMap
from ..common.text import RedactedText
from .base import BaseInspectDriver

logger = logging.getLogger(__name__)


class InspectAnnotationsConfig(BaseModel):
    engine: Literal["inspect:annotations"]

    @cached_property
    def driver(self) -> "InspectAnnotationsDriver":
        return InspectAnnotationsDriver(self)


class InspectAnnotationsDriver(BaseInspectDriver):
    """An inspect driver that infers annotations from redacted text.

    This driver is used to infer annotations from redacted text. The annotations
    are stored in the context object, and can be referenced from other parts of
    the pipeline.
    """

    def __init__(self, config: InspectAnnotationsConfig):
        self.config = config

    def __call__(
        self,
        input: RedactedText,
        context: Context,
        subjects: IdToNameMap | None = None,
        placeholders: NameToMaskMap | None = None,
    ) -> RedactedText:
        """Infer annotations from redacted text."""

        # Remove any hanging redactions in truncated results.
        redaction = input.redacted
        if input.truncated:
            redaction = remove_hanging_redactions(
                input.redacted, raw_delimiters=input.delimiters
            )

        annotations = infer_annotations(
            input.original, redaction, delimiters=input.delimiters
        )

        context.annotations = list(annotations)

        return input
