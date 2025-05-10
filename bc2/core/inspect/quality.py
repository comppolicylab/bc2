from dataclasses import dataclass, field
from functools import cached_property
from typing import Literal

from pydantic import BaseModel

from ..common.context import Context
from ..common.infer import segment
from ..common.name_map import IdToNameMap, NameToMaskMap
from ..common.text import RedactedText
from .base import BaseInspectDriver


class InspectQualityConfig(BaseModel):
    engine: Literal["inspect:quality"]
    optional: bool = True

    @cached_property
    def driver(self) -> "InspectQualityDriver":
        return InspectQualityDriver(self)


@dataclass
class QualityMetric:
    valid: int = 0
    invalid: int = 0
    n: int = 0

    @property
    def p_valid(self) -> float:
        return self.valid / self.n


@dataclass
class QualityReport:
    """Quality metrics for the redacted text.

    The difference between `segments` and `edits` is that `segments` includes
    unaltered text between the original and redacted versions, while `edits`
    only considers text that was changed between the two.

    Both `segments.invalid` and `edits.invalid` will be the same, since invalid
    segments are by definition also edits. But the ratios of invalid to valid
    for these two metrics will almost always be different.

    Attributes:
        segments: The number of segments in the redacted text.
        chars: The number of characters in the redacted text.
        edits: The number of edits in the redacted text.
    """

    segments: QualityMetric = field(default_factory=QualityMetric)
    chars: QualityMetric = field(default_factory=QualityMetric)
    edits: QualityMetric = field(default_factory=QualityMetric)


class InspectQualityDriver(BaseInspectDriver):
    """Compute stats about the quality of the redacted text."""

    def __init__(self, config: InspectQualityConfig):
        self.config = config

    def __call__(
        self,
        input: RedactedText,
        context: Context,
        subjects: IdToNameMap | None = None,
        placeholders: NameToMaskMap | None = None,
    ) -> RedactedText:
        """Compute some quality metrics about the redacted text.

        Stores result in `context.quality`.
        """
        quality = QualityReport()
        for ts in segment(input.original, input.redacted, delimiters=input.delimiters):
            quality.segments.n += 1
            quality.chars.n += len(ts.redacted.text)
            quality.edits.n += 1 if ts.is_edit else 0
            if ts.is_valid:
                quality.segments.valid += 1
                quality.chars.valid += len(ts.redacted.text)
                quality.edits.valid += 1 if ts.is_edit else 0
            else:
                quality.segments.invalid += 1
                quality.chars.invalid += len(ts.redacted.text)
                quality.edits.invalid += 1 if ts.is_edit else 0
        context.quality = quality
        return input
