import pytest

from ..common.context import Context
from ..common.text import RedactedText
from .annotations import InspectAnnotationsConfig


@pytest.mark.parametrize(
    "original, redacted, expected",
    [
        (
            "Hello, world!",
            "Hello, [Person 1]!",
            [
                {
                    "content": "[Person 1]",
                    "end": 12,
                    "start": 7,
                    "original": "world",
                    "redacted": "Person 1",
                }
            ],
        ),
        (
            "Leopold is first, then Pollock, then Abbott, then Leopold again.",
            (
                "[Subject 1] is first, "
                "then [Subject 2], then [Subject 3], "
                "then [Subject 1] again."
            ),
            [
                {
                    "start": 0,
                    "end": 7,
                    "content": "[Subject 1]",
                    "original": "Leopold",
                    "redacted": "Subject 1",
                },
                {
                    "start": 23,
                    "end": 30,
                    "content": "[Subject 2]",
                    "original": "Pollock",
                    "redacted": "Subject 2",
                },
                {
                    "start": 37,
                    "end": 43,
                    "content": "[Subject 3]",
                    "original": "Abbott",
                    "redacted": "Subject 3",
                },
                {
                    "start": 50,
                    "end": 57,
                    "content": "[Subject 1]",
                    "original": "Leopold",
                    "redacted": "Subject 1",
                },
            ],
        ),
    ],
)
def test_render_text(original, redacted, expected):
    cfg = InspectAnnotationsConfig.model_validate(
        {
            "engine": "inspect:annotations",
        }
    )
    rt = RedactedText(redacted, original, "[]")
    ctx = Context()
    result = cfg.driver(rt, ctx)
    assert result == rt
    assert ctx.annotations == expected
