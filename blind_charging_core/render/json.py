import json
from functools import cached_property
from typing import Literal

from ..common.context import Context
from ..common.file import MemoryFile
from ..common.infer import TextSegment
from ..common.text import RedactedText
from .base import BaseRenderConfig, BaseRenderer


class JsonRenderConfig(BaseRenderConfig):
    """JSON Render config."""

    engine: Literal["render:json"] = "render:json"

    @cached_property
    def driver(self) -> "JsonRenderer":
        return JsonRenderer(self)


def format_annotation(annotation: TextSegment) -> dict:
    """Condense the annotation into a simpler JSON format."""
    return {
        "originalSpan": [annotation.original.start, annotation.original.end],
        "redactedSpan": [annotation.redacted.start, annotation.redacted.end],
        "valid": annotation.is_valid,
        "openDelim": annotation.open_delim,
        "closeDelim": annotation.close_delim,
    }


class JsonRenderer(BaseRenderer):
    def __init__(self, config: JsonRenderConfig) -> None:
        self.config = config

    def __call__(self, redaction: RedactedText, context: Context) -> MemoryFile:
        f = MemoryFile()

        f.write(
            json.dumps(
                {
                    "original": redaction.original,
                    "redacted": redaction.redacted,
                    "annotations": [
                        format_annotation(a) for a in redaction.annotations
                    ],
                }
            )
        )

        return f
