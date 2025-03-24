import json
from unittest.mock import patch

from ..common.context import Context
from ..common.datafile import DataType, load_data_file
from ..common.name_map import IdToMaskMap, IdToNameMap
from ..common.text import RedactedText
from .masked_subjects import OpenAIMaskedSubjectsInspectConfig

masked_subjects_prompt = load_data_file(DataType.prompt, "subject_masks")


@patch("bc2.core.common.openai.OpenAI")
def test_inspect_subject_masks(openai_mock):
    cfg = OpenAIMaskedSubjectsInspectConfig.model_validate(
        {
            "engine": "inspect:subject_masks",
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
        subjects=IdToNameMap(
            {
                "A": "Leopold",
                "B": "Pollock",
                "C": "Abbott",
            }
        ),
    )
    assert result == rt
    assert ctx.masked_subjects == IdToMaskMap(
        {
            "A": "Subject 1",
            "B": "Subject 2",
            "C": "Subject 3",
        }
    )
    openai_mock.return_value.chat.completions.create.assert_called_once_with(
        model="gpt-4o",
        n=1,
        max_tokens=None,
        messages=[
            {
                "role": "system",
                "content": masked_subjects_prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "[COLLECTION#1]\n"
                            "<Names>"
                            "<Name>"
                            "<ID>A</ID><RealName>Leopold</RealName>"
                            "</Name>"
                            "<Name>"
                            "<ID>B</ID><RealName>Pollock</RealName>"
                            "</Name>"
                            "<Name>"
                            "<ID>C</ID><RealName>Abbott</RealName>"
                            "</Name>"
                            "</Names>\n\n"
                            "[COLLECTION#2]\n"
                            "<Names>"
                            "<Name>"
                            "<RealName>Leopold</RealName>"
                            "<ReplacementText>Subject 1</ReplacementText>"
                            "</Name>"
                            "<Name>"
                            "<RealName>Pollock</RealName>"
                            "<ReplacementText>Subject 2</ReplacementText>"
                            "</Name>"
                            "<Name>"
                            "<RealName>Abbott</RealName>"
                            "<ReplacementText>Subject 3</ReplacementText>"
                            "</Name>"
                            "</Names>\n\n"
                            "[NARRATIVE]\n"
                            "Leopold is first, then Pollock, then Abbott, "
                            "then Poldy again."
                        ),
                    }
                ],
            },
        ],
    )
