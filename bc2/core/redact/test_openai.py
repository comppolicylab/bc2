from unittest.mock import MagicMock, patch

import pytest
from openai.types.responses import ResponseInputText

from ..common.context import Context
from ..common.name_map import NameToMaskMap
from ..common.text import RedactedText, Text
from .base import MissingNarrativeError
from .openai import OpenAIRedactConfig

JINJA_PROMPT_WITH_PLACEHOLDERS = """\
Prompt with jinja formatting placeholders.

{% for item in placeholders.to_json() %}
{{ item["ReplacementText"] }} is {{ item["RealName"] }}
{% endfor %}
"""

STRING_PROMPT_WITH_PLACEHOLDERS = """\
The xml is:

{placeholders_xml}\
"""


@patch("bc2.core.common.openai.OpenAI")
def test_redact_jinja_with_placeholders(openai_mock):
    def mock_create(*args, **kwargs):
        model_name = kwargs.get("model")
        if model_name == "resolver_model":
            response = MagicMock()
            response.output_text = "{}"
            response.status = "completed"
            response.usage = type("Usage", (), {"output_tokens": 10})()
            response.incomplete_details = None
            response.output_parsed = None
            response.error = None
            return response
        else:
            response = MagicMock()
            response.output_text = (
                "Subject 1, Subject 2, and Subject 3 went to the store."
            )
            response.status = "completed"
            response.usage = type("Usage", (), {"output_tokens": 10})()
            response.incomplete_details = None
            response.output_parsed = None
            response.error = None
            return response

    openai_mock.return_value.responses.create.side_effect = mock_create

    cfg = OpenAIRedactConfig.model_validate(
        {
            "engine": "redact:openai",
            "delimiters": ("[", "]"),
            "client": {
                "api_key": "abc123",
                "base_url": "http://openai.local",
            },
            "generator": {
                "method": "chat",
                "model": "gpt-4o-2024-05-13",
                "system": {
                    "engine": "jinja",
                    "prompt": JINJA_PROMPT_WITH_PLACEHOLDERS,
                },
            },
        },
    )

    result = cfg.driver(
        narrative=Text("Leopold, Pollock, and Abbott went to the store."),
        context=Context(),
        placeholders=NameToMaskMap(
            {
                "Leopold": "Subject 1",
                "Pollock": "Subject 2",
                "Abbott": "Subject 3",
            }
        ),
    )
    assert result == RedactedText(
        "Subject 1, Subject 2, and Subject 3 went to the store.",
        "Leopold, Pollock, and Abbott went to the store.",
        ("[", "]"),
    )
    openai_mock.return_value.responses.create.assert_called_once_with(
        model="gpt-4o-2024-05-13",
        max_output_tokens=4_096,
        store=False,
        input=[
            {
                "role": "system",
                "content": (
                    "Prompt with jinja formatting placeholders.\n\n\n"
                    "Subject 1 is Leopold\n\nSubject 2 is Pollock\n\n"
                    "Subject 3 is Abbott\n"
                ),
            },
            {
                "role": "user",
                "content": [
                    ResponseInputText.model_validate(
                        {
                            "type": "input_text",
                            "text": "Leopold, Pollock, and Abbott went to the store.",
                        }
                    )
                ],
            },
        ],
    )


@patch("bc2.core.common.openai.OpenAI")
def test_redact_string_with_placeholders(openai_mock):
    def mock_create(*args, **kwargs):
        model_name = kwargs.get("model")
        if model_name == "resolver_model":
            response = MagicMock()
            response.output_text = "{}"
            response.status = "completed"
            response.usage = type("Usage", (), {"output_tokens": 10})()
            response.incomplete_details = None
            response.output_parsed = None
            response.error = None
            return response
        else:
            response = MagicMock()
            response.output_text = (
                "Subject 1, Subject 2, and Subject 3 went to the store."
            )
            response.status = "completed"
            response.usage = type("Usage", (), {"output_tokens": 10})()
            response.incomplete_details = None
            response.output_parsed = None
            response.error = None
            return response

    openai_mock.return_value.responses.create.side_effect = mock_create

    cfg = OpenAIRedactConfig.model_validate(
        {
            "engine": "redact:openai",
            "delimiters": ("{", "}"),
            "client": {
                "api_key": "abc123",
                "base_url": "http://openai.local",
            },
            "generator": {
                "method": "chat",
                "model": "gpt-4o-2024-05-13",
                "system": {
                    "engine": "string",
                    "prompt": STRING_PROMPT_WITH_PLACEHOLDERS,
                },
            },
        },
    )

    placeholders = NameToMaskMap(
        {
            "Leopold": "Subject 1",
            "Pollock": "Subject 2",
            "Abbott": "Subject 3",
        }
    )

    result = cfg.driver(
        narrative=Text("Leopold, Pollock, and Abbott went to the store."),
        context=Context(),
        placeholders=placeholders,
    )
    assert result == RedactedText(
        "Subject 1, Subject 2, and Subject 3 went to the store.",
        "Leopold, Pollock, and Abbott went to the store.",
        ("{", "}"),
    )
    openai_mock.return_value.responses.create.assert_called_once_with(
        model="gpt-4o-2024-05-13",
        max_output_tokens=4_096,
        store=False,
        input=[
            {
                "role": "system",
                "content": (
                    """\
The xml is:

<Names><Name><RealName>Leopold</RealName>\
<ReplacementText>Subject 1</ReplacementText></Name>\
<Name><RealName>Pollock</RealName><ReplacementText>Subject 2</ReplacementText>\
</Name><Name><RealName>Abbott</RealName>\
<ReplacementText>Subject 3</ReplacementText></Name></Names>\
"""
                ),
            },
            {
                "role": "user",
                "content": [
                    ResponseInputText.model_validate(
                        {
                            "type": "input_text",
                            "text": "Leopold, Pollock, and Abbott went to the store.",
                        }
                    )
                ],
            },
        ],
    )


@pytest.mark.parametrize("narrative", ["", "No narratives found."])
@patch("bc2.core.common.openai.OpenAI")
def test_redact_raises_on_empty_narrative(openai_mock, narrative):
    cfg = OpenAIRedactConfig.model_validate(
        {
            "engine": "redact:openai",
            "delimiters": ("[", "]"),
            "client": {
                "api_key": "abc123",
                "base_url": "http://openai.local",
            },
            "generator": {
                "method": "chat",
                "model": "gpt-4o-2024-05-13",
                "system": {
                    "engine": "string",
                    "prompt": "Redact the text.",
                },
            },
        },
    )

    with pytest.raises(MissingNarrativeError):
        cfg.driver(
            narrative=Text(narrative),
            context=Context(),
            placeholders=NameToMaskMap({"Leopold": "Subject 1"}),
        )

    openai_mock.return_value.responses.parse.assert_not_called()
    openai_mock.return_value.responses.create.assert_not_called()
