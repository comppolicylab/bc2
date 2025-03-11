import pytest

from ..common.context import Context
from ..common.text import RedactedText
from .quality import InspectQualityConfig, QualityMetric, QualityReport


@pytest.mark.parametrize(
    "original, redacted, expected",
    [
        (
            "Hello, world!",
            "Hello, [Person 1]!",
            QualityReport(
                segments=QualityMetric(valid=3, invalid=0, n=3),
                chars=QualityMetric(valid=18, invalid=0, n=18),
                edits=QualityMetric(valid=1, invalid=0, n=1),
            ),
        ),
        (
            "Hello, world!",
            "Helloz, [Person 1]!",
            QualityReport(
                segments=QualityMetric(valid=4, invalid=1, n=5),
                chars=QualityMetric(valid=18, invalid=1, n=19),
                edits=QualityMetric(valid=1, invalid=1, n=2),
            ),
        ),
    ],
)
def test_inspect_quality(original, redacted, expected):
    cfg = InspectQualityConfig.model_validate(
        {
            "engine": "inspect:quality",
        }
    )
    rt = RedactedText(redacted, original, "[]")
    ctx = Context()
    result = cfg.driver(rt, ctx)
    assert result == rt
    assert ctx.quality == expected
