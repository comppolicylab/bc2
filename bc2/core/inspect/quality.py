from dataclasses import dataclass
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
class Quality:
    n_segments: int = 0
    valid_segments: int = 0
    invalid_segments: int = 0
    valid_chars: int = 0
    invalid_chars: int = 0
    n_chars: int = 0

    @property
    def p_valid_segments(self) -> float:
        return self.valid_segments / self.n_segments

    @property
    def p_valid_chars(self) -> float:
        return self.valid_chars / self.n_chars


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
        quality = Quality()
        for ts in segment(input.original, input.redacted, delimiters=input.delimiters):
            quality.n_segments += 1
            quality.n_chars += len(ts.redacted.text)
            if ts.is_valid:
                quality.valid_segments += 1
                quality.valid_chars += len(ts.redacted.text)
            else:
                quality.invalid_segments += 1
                quality.invalid_chars += len(ts.redacted.text)
        context.quality = quality
        return input
