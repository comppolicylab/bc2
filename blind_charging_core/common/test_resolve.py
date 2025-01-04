import pytest

from .resolve import prepare_resolve_input


@pytest.mark.parametrize(
    "original,redacted,aliases,raw_delimiters,expected",
    [
        (
            "One day, Leopold trotted into Safeway to buy a big bone.",
            "One day, <Dog 1> trotted into <Store 1> to buy a big bone.",
            {"Leopold": "Dog 1"},
            "<>",
            """\
[MAP#1]
{
  "Leopold": "Dog 1"
}

[MAP#2]
{
  "Leopold": "Dog 1",
  "Safeway": "Store 1"
}

[NARRATIVE]
One day, Leopold trotted into Safeway to buy a big bone.
""",
        ),
        (
            "One day, the best dog trotted into a store to buy a big bone.",
            "One day, the best dog trotted into a store to buy a big bone.",
            {"Leopold": "Dog 1"},
            "<>",
            """\
[MAP#1]
{
  "Leopold": "Dog 1"
}

[MAP#2]
{}

[NARRATIVE]
One day, the best dog trotted into a store to buy a big bone.
""",
        ),
        (
            "One day, Leopold trotted into Safeway to buy a big bone.",
            "One day, <Dog 1> trotted into <Store 1> to buy a big bone.",
            None,
            "<>",
            """\
[MAP#1]
{}

[MAP#2]
{
  "Leopold": "Dog 1",
  "Safeway": "Store 1"
}

[NARRATIVE]
One day, Leopold trotted into Safeway to buy a big bone.
""",
        ),
    ],
)
def test_prepare_resolve_input(original, redacted, aliases, raw_delimiters, expected):
    assert (
        prepare_resolve_input(original, redacted, aliases, raw_delimiters) == expected
    )
