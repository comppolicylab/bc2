import pytest

from .infer import infer_annotations, remove_hanging_redactions


@pytest.mark.parametrize(
    "original,redacted,delimiters,expected",
    [
        (
            "Hello, world!",
            "Hello, <name>!",
            "<>",
            [
                {
                    "start": 7,
                    "end": 12,
                    "content": "<name>",
                    "original": "world",
                    "redacted": "name",
                }
            ],
        ),
        (
            "Hello, world!",
            "Hello, [name]!",
            "[]",
            [
                {
                    "start": 7,
                    "end": 12,
                    "content": "[name]",
                    "original": "world",
                    "redacted": "name",
                }
            ],
        ),
        (
            "Hello, world!",
            "Hello, [name]!",
            "<>",
            [],  # Delimiters don't match so nothing is found
        ),
        (
            """\
Just a test narrative where there's nothing very interesting to redact.

My dog Leopold and I were walking in Golden Gate Park last night, \
near 9th Avenue and Lincoln. \
We passed a mother and her son speaking Russian together. \
Leopold really wanted to clean their ears but I wouldn't let him.
""",
            """\
Just a test narrative where there's nothing very interesting to redact.

My dog <(D1)> and I were walking in <location> last night, near <location>. \
We passed a mother and her son speaking <language> together. \
<(D1)> really wanted to clean their ears but I wouldn't let him.
""",
            "<>",
            [
                {
                    "start": 80,
                    "end": 87,
                    "content": "<(D1)>",
                    "original": "Leopold",
                    "redacted": "(D1)",
                },
                {
                    "start": 110,
                    "end": 126,
                    "content": "<location>",
                    "original": "Golden Gate Park",
                    "redacted": "location",
                },
                {
                    "start": 144,
                    "end": 166,
                    "content": "<location>",
                    "original": "9th Avenue and Lincoln",
                    "redacted": "location",
                },
                {
                    "start": 208,
                    "end": 215,
                    "content": "<language>",
                    "original": "Russian",
                    "redacted": "language",
                },
                {
                    "start": 226,
                    "end": 233,
                    "content": "<(D1)>",
                    "original": "Leopold",
                    "redacted": "(D1)",
                },
            ],
        ),
    ],
)
def test_infer_annotations(original, redacted, delimiters, expected):
    assert (
        list(infer_annotations(original, redacted, delimiters=delimiters)) == expected
    )


@pytest.mark.parametrize(
    "redacted,raw_delimiters,expected",
    [
        (
            "Hello, world!",
            "<>",
            "Hello, world!",
        ),
        (
            "Hello, <World",
            "<>",
            "Hello, ",
        ),
        (
            "<Hello 1>, <World",
            "<>",
            "<Hello 1>, ",
        ),
        (
            "Hello, <World 1>!",
            "<>",
            "Hello, <World 1>!",
        ),
    ],
)
def test_remove_hanging_redactions(redacted, raw_delimiters, expected):
    assert remove_hanging_redactions(redacted, raw_delimiters) == expected
