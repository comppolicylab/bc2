from unittest.mock import MagicMock, patch

from ..common.context import Context
from ..common.text import RedactedText, Text
from .openai import OpenAIRedactConfig

JINJA_PROMPT_WITH_ALIASES = """\
Prompt with jinja formatting aliases.

{% for k, v in preset_aliases.items() %}
{{ k }} is {{ v }}
{% endfor %}
"""


@patch("bc2.core.common.openai.OpenAI")
def test_redact_jinja_with_aliases(openai_mock):
    def mock_create(*args, **kwargs):
        model_name = kwargs.get("model")
        if model_name == "resolver_model":
            response = MagicMock()
            response.choices = [MagicMock(message=MagicMock(content="{}"))]
            return response
        else:
            response = MagicMock()
            response.choices = [
                MagicMock(
                    message=MagicMock(
                        content="Subject 1, Subject 2, and Subject 3 went to the store."
                    )
                )
            ]
            return response

    openai_mock.return_value.chat.completions.create.side_effect = mock_create

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
                "model": "gpt-4o",
                "system": {
                    "engine": "jinja",
                    "prompt": JINJA_PROMPT_WITH_ALIASES,
                },
            },
            "resolver": {
                "method": "chat",
                "model": "resolver_model",
                "system": {
                    "engine": "string",
                    "prompt": "This is the resolver prompt.",
                },
            },
        },
    )

    result = cfg.driver(
        narrative=Text("Leopold, Pollock, and Abbott went to the store."),
        context=Context(),
        aliases={
            "Subject 1": "Leopold",
            "Subject 2": "Pollock",
            "Subject 3": "Abbott",
        },
    )
    assert result == RedactedText(
        "Subject 1, Subject 2, and Subject 3 went to the store.",
        "Leopold, Pollock, and Abbott went to the store.",
        ("[", "]"),
    )
    assert openai_mock.return_value.chat.completions.create.call_count == 2
    openai_mock.return_value.chat.completions.create.assert_any_call(
        model="gpt-4o",
        n=1,
        messages=[
            {
                "role": "system",
                "content": (
                    "Prompt with jinja formatting aliases.\n\n\n"
                    "Subject 1 is Leopold\n\nSubject 2 is Pollock\n\n"
                    "Subject 3 is Abbott\n"
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Leopold, Pollock, and Abbott went to the store.",
                    }
                ],
            },
        ],
    )
    openai_mock.return_value.chat.completions.create.assert_any_call(
        model="resolver_model",
        n=1,
        messages=[
            {
                "role": "system",
                "content": "This is the resolver prompt.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "[MAP#1]\n{\n"
                            '  "Subject 1": "Leopold",\n'
                            '  "Subject 2": "Pollock",\n'
                            '  "Subject 3": "Abbott"\n'
                            "}\n\n"
                            "[MAP#2]\n{}\n\n"
                            "[NARRATIVE]\n"
                            "Leopold, Pollock, and Abbott went to the store.\n"
                        ),
                    }
                ],
            },
        ],
    )
