import pytest

from .align import residual


@pytest.mark.parametrize(
    "original,extract,expected",
    [
        (
            "One day, Leopold trotted into Safeway to buy a big bone.",
            "One day, Leopold trotted",
            " into Safeway to buy a big bone.",
        ),
        (
            "One day, Leopold trotted into Safeway to buy a big bone.",
            "One day, Leopold trotted into Safeway to buy a big bone.",
            "",
        ),
        (
            "One day, Leopold trotted into Safeway to buy a big bone.",
            "Then he went to the park to look for squirrels.",
            None,
        ),
    ],
)
def test_residual(original, extract, expected):
    assert residual(original, extract) == expected
