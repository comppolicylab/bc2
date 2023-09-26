import pytest

from .infer import infer_annotations


@pytest.mark.parametrize(
    "original,redacted,expected",
    [
        (
            "Hello, world!",
            "Hello, <name>!",
            [{"start": 7, "end": 12, "content": "<name>"}],
        ),
    ],
)
def test_infer_annotations(original, redacted, expected):
    assert infer_annotations(original, redacted) == expected
