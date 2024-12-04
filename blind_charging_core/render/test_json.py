import json

import pytest

from ..common.context import Context
from ..common.text import RedactedText
from .json import JsonRenderConfig


@pytest.mark.parametrize(
    "original, redacted, annotations",
    [
        (
            "Hello, world!",
            "Hello, [Person 1]!",
            [
                {
                    "originalSpan": [7, 12],
                    "redactedSpan": [7, 17],
                    "valid": True,
                    "openDelim": "[",
                    "closeDelim": "]",
                }
            ],
        ),
        (
            "I took photos of Leopold's ears.",
            "I took photos of [Subject 1]'s ears!",
            [
                {
                    "originalSpan": [17, 24],
                    "redactedSpan": [17, 28],
                    "valid": True,
                    "openDelim": "[",
                    "closeDelim": "]",
                },
                {
                    "originalSpan": [31, 32],
                    "redactedSpan": [35, 36],
                    "valid": False,
                    "openDelim": None,
                    "closeDelim": None,
                },
            ],
        ),
    ],
)
def test_render_json(original, redacted, annotations):
    cfg = JsonRenderConfig.model_validate(
        {
            "engine": "render:json",
        }
    )
    rt = RedactedText(redacted, original, "[]")
    ctx = Context()

    result = cfg.driver(rt, ctx)
    assert json.loads(result.content()) == {
        "redacted": redacted,
        "original": original,
        "annotations": annotations,
    }
