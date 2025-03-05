from dataclasses import dataclass, field
from functools import cached_property
from typing import Literal

from pydantic import BaseModel

from ..common.context import Context
from ..common.infer import segment
from ..common.text import RedactedText
from ..common.types import NameMap
from .base import BaseInspectDriver


class InspectQualityConfig(BaseModel):
    engine: Literal["inspect:quality"]

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
    segments: QualityMetric = field(default_factory=QualityMetric)
    chars: QualityMetric = field(default_factory=QualityMetric)
    edits: QualityMetric = field(default_factory=QualityMetric)


class InspectQualityDriver(BaseInspectDriver):
    """ """

    def __init__(self, config: InspectQualityConfig):
        self.config = config

    def __call__(
        self, input: RedactedText, context: Context, subjects: NameMap | None = None
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
