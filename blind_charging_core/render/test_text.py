import pytest

from ..common.context import Context
from ..common.text import RedactedText
from .text import TextRenderConfig


def decorate(txt: str) -> bytes:
    """Add the disclaimer header / footer to the given text."""
    header = (
        b"Redacted Narrative for Race-Blind Charging\n\n\n=== NARRATIVE ===\n"
    )
    footer = (
        b"\n\n\n---------------------------------------------------------------"
        b"---------------------------------------------------------------------"
        b"--------------------------"
        b"The above passages have been automatically extracted from referral "
        b"documents and automatically redacted to hide race-related "
        b"information. In rare circumstances, words or punctuation may be "
        b"automatically added to fix typos. These additions will appear in "
        b"light grey. Please report any issues to "
        b"blind_charging@hks.harvard.edu."
        b"\n\n\n=== END OF DOCUMENT ===\n"
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
        }
    )
    rt = RedactedText(redacted, original, "[]")
    ctx = Context()
    if debug:
        ctx.debug = True

    result = cfg.driver(rt, ctx)
    assert result.content() == decorate(expected)
