from unittest.mock import patch

from ..common.text import RedactedText, Text
from .openai import OpenAIRedactConfig

JINJA_PROMPT_WITH_ALIASES = """\
Prompt with jinja formatting aliases.

{% for k, v in aliases.items() %}
{{ k }} is {{ v }}
{% endfor %}
"""


@patch("blind_charging_core.common.openai.OpenAI")
def test_redact_jinja_with_aliases(openai_mock):
    openai_mock.return_value.chat.completions.create.return_value.choices[
        0
    ].message.content = "Subject 1, Subject 2, and Subject 3 went to the store."

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
                "temperature": 0.5,
                "seed": 42,
                "system": {
                    "engine": "jinja",
                    "prompt": JINJA_PROMPT_WITH_ALIASES,
                },
            },
        },
    )

    result = cfg.driver(
        narrative=Text("Leopold, Pollock, and Abbott went to the store."),
        preset_aliases={
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
    openai_mock.return_value.chat.completions.create.assert_called_once_with(
        model="gpt-4o",
        n=1,
        seed=42,
        temperature=0.5,
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
