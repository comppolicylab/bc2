import json

import pytest

from ..common.context import Context
from ..common.text import RedactedText
from .json import JsonRenderConfig


@pytest.mark.parametrize(
    "original, redacted",
    [
        (
            "Hello, world!",
            "Hello, [Person 1]!",
        ),
        (
            "I took photos of Leopold ears.",
            "I took photos of [Subject 1]'s ears.",
        ),
    ],
)
def test_render_json(original, redacted):
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
    }
