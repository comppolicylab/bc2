import pytest

from .validate import validate_json


@pytest.mark.parametrize(
    "raw,expected",
    [
        (
            '{\n  "key": "value"\n}',
            {"key": "value"},
        )
    ],
)
def test_validate_json(raw, expected):
    assert validate_json(raw) == expected


def test_validate_json_invalid():
    invalid_json = "I'm a finicky language model, \
      I'm not going to comply with your request!"
    with pytest.raises(ValueError, match="Error parsing JSON response."):
        validate_json(invalid_json)
