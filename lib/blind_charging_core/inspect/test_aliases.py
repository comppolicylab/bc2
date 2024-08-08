import json
from unittest.mock import patch

from ..common.context import Context
from ..common.text import RedactedText
from .aliases import ALIASES_SYSTEM_TPL, OpenAIAliasesInspectConfig


@patch("blind_charging_core.common.openai.OpenAI")
def test_inspect_aliases(openai_mock):
    cfg = OpenAIAliasesInspectConfig.model_validate(
        {
            "engine": "inspect:aliases",
            "client": {
                "api_key": "abc123",
                "base_url": "http://openai.local",
            },
            "generator": {
                "model": "gpt-4o",
            },
        },
    )
    rt = RedactedText(
        (
            "[Subject 1] is first, then [Subject 2], "
            "then [Subject 3], then [Subject 1] again."
        ),
        "Leopold is first, then Pollock, then Abbott, then Poldy again.",
        "[]",
    )
    ctx = Context()
    ctx.annotations = [
        {
            "start": 0,
            "end": 7,
            "content": "[Subject 1]",
            "original": "Leopold",
            "redacted": "Subject 1",
        },
        {
            "start": 23,
            "end": 30,
            "content": "[Subject 2]",
            "original": "Pollock",
            "redacted": "Subject 2",
        },
        {
            "start": 37,
            "end": 43,
            "content": "[Subject 3]",
            "original": "Abbott",
            "redacted": "Subject 3",
        },
        {
            "start": 50,
            "end": 57,
            "content": "[Subject 1]",
            "original": "Leopold",
            "redacted": "Subject 1",
        },
    ]

    openai_mock.return_value.chat.completions.create.return_value.choices[
        0
    ].message.content = json.dumps(
        {
            "A": "Subject 1",
            "B": "Subject 2",
            "C": "Subject 3",
        }
    )

    result = cfg.driver(
        rt,
        ctx,
        subjects={
            "A": "Leopold",
            "B": "Pollock",
            "C": "Abbott",
        },
    )
    assert result == rt
    assert ctx.aliases == {
        "A": "Subject 1",
        "B": "Subject 2",
        "C": "Subject 3",
    }
    openai_mock.return_value.chat.completions.create.assert_called_once_with(
        model="gpt-4o",
        n=1,
        messages=[
            {
                "role": "system",
                "content": ALIASES_SYSTEM_TPL,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "[MAP#1]\n"
                            '{\n  "A": "Leopold",\n  "B": "Pollock",\n  '
                            '"C": "Abbott"\n}\n\n'
                            "[MAP#2]\n"
                            '{\n  "Abbott": "Subject 3",\n  "Leopold": "Subject 1",'
                            '\n  "Pollock": "Subject 2"\n}\n\n'
                            "[NARRATIVE]\n"
                            "Leopold is first, then Pollock, then Abbott, "
                            "then Poldy again."
                        ),
                    }
                ],
            },
        ],
    )
