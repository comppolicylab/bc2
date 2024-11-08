import pytest

from ..common.context import Context
from ..common.text import RedactedText
from .text import TextRenderConfig


def decorate(txt: str) -> bytes:
    """Add the disclaimer header / footer to the given text."""
    header = b"=== Redacted Narrative for Race-Blind Charging ===\n\n\n"
    footer = (
        b"\n\n\n---------------------------------------------------------\n"
        b"The above passages were automatically extracted from referral "
        b"documents and automatically redacted to hide race-related "
        b"information. Occasionally, words or punctuation may be "
        b"automatically added to fix typos. Please report any issues to "
        b"blind_charging@hks.harvard.edu."
    )
    return header + txt.encode("utf-8") + footer


@pytest.mark.parametrize(
    "original, redacted, expected, debug",
    [
        (
            "Hello, world!",
            "Hello, [Person 1]!",
            "Hello, [Person 1]!",
            False,
        ),
        (
            "I took photos of Leopold ears.",
            "I took photos of [Subject 1]'s ears.",
            "I took photos of [Leopold -> Subject 1]'s ears.",
            True,
        ),
    ],
)
def test_render_text(original, redacted, expected, debug):
    cfg = TextRenderConfig.model_validate(
        {
            "engine": "render:text",
            "header": True,
            "footer": True,
        }
    )
    rt = RedactedText(redacted, original, "[]")
    ctx = Context()
    if debug:
        ctx.debug = True

    result = cfg.driver(rt, ctx)
    assert result.content() == decorate(expected)
