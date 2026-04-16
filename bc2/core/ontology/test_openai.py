import json
from unittest.mock import MagicMock, patch

import pytest
from azure.ai.documentintelligence.models import AnalyzeResult
from openai import OpenAI
from openai.types.responses import ResponseInputText

from ..common.context import Context
from ..common.file import MemoryFile
from ..common.ontology import (
    Cited,
    Offense,
    PoliceReport,
    Subject,
)
from .base import EmptyOntologyError
from .openai import OpenAIOntologyConfig


def _make_report() -> PoliceReport:
    return PoliceReport(
        reporting_agency=Cited(ids=[0], content="SFPD"),
        case_number=Cited(ids=[0], content="2024-0001"),
        location=Cited(ids=[1], content="101 Main St"),
        incident_type=Cited(ids=[1], content="Theft"),
        subjects=[
            Subject(
                seq=Cited(ids=[2], content=1),
                type=Cited(ids=[2], content="Victim"),
                name=Cited(ids=[2], content="Leopold"),
                address=Cited(ids=[2], content="101 Main St"),
                phone=Cited(ids=[2], content="555-1234"),
                race=Cited(ids=[2], content="Unknown"),
                sex=Cited(ids=[2], content="M"),
                dob=Cited(ids=[2], content="1990-01-01"),
            )
        ],
        narratives=[Cited(ids=[3], content="Incident narrative here.")],
        offenses=[
            Offense(
                crime=Cited(ids=[1], content="Theft"),
                statute=None,
                code=None,
            )
        ],
    )


def _analyze_result_dict() -> dict:
    return {
        "paragraphs": [
            {
                "content": "Reporting Agency: SFPD",
                "spans": [{"offset": 0, "length": 22}],
                "boundingRegions": [
                    {
                        "pageNumber": 1,
                        "polygon": [0, 0, 4.25, 0, 4.25, 0.5, 0, 0.5],
                    }
                ],
            },
            {
                "content": "Incident: Theft at 101 Main St",
                "spans": [{"offset": 24, "length": 30}],
                "boundingRegions": [
                    {
                        "pageNumber": 1,
                        "polygon": [0, 1.0, 8.5, 1.0, 8.5, 1.5, 0, 1.5],
                    }
                ],
            },
            {
                "content": "Narrative paragraph on page 2.",
                "spans": [{"offset": 56, "length": 30}],
                "boundingRegions": [
                    {
                        "pageNumber": 2,
                        "polygon": [0, 0, 8.5, 0, 8.5, 11.0, 0, 11.0],
                    }
                ],
            },
        ],
        "pages": [
            {"pageNumber": 1, "width": 8.5, "height": 11.0},
            {"pageNumber": 2, "width": 8.5, "height": 11.0},
        ],
    }


def _make_config() -> OpenAIOntologyConfig:
    return OpenAIOntologyConfig.model_validate(
        {
            "engine": "ontology:openai",
            "client": {
                "api_key": "abc123",
                "base_url": "http://openai.local",
            },
            "generator": {
                "method": "chat",
                "model": "gpt-4o-2024-05-13",
                "system": {
                    "engine": "string",
                    "prompt": "Extract the ontology.",
                },
            },
        },
    )


def _mock_parse_response(parsed: PoliceReport | None) -> MagicMock:
    response = MagicMock()
    response.output_text = parsed.model_dump_json() if parsed is not None else ""
    response.output_parsed = parsed
    response.status = "completed"
    response.usage = type("Usage", (), {"output_tokens": 10})()
    response.incomplete_details = None
    response.error = None
    return response


def _install_openai_mock(
    openai_mock: MagicMock, parsed: PoliceReport | None
) -> MagicMock:
    """Install a spec'd OpenAI client as the return value of the patched class.

    Using `spec=OpenAI` ensures that `hasattr(client, 'mime_type')` is False so
    the preprocessor mixin does not confuse the client with a preprocessor
    method while iterating driver attributes.
    """
    client = MagicMock(spec=OpenAI)
    client.responses.parse.return_value = _mock_parse_response(parsed)
    openai_mock.return_value = client
    return client


@patch("bc2.core.common.openai.OpenAI")
def test_extract_formats_xml_and_builds_chunks(openai_mock):
    report = _make_report()
    client = _install_openai_mock(openai_mock, report)

    cfg = _make_config()

    analyze_result = AnalyzeResult(_analyze_result_dict())
    result = cfg.driver.extract(analyze_result)

    assert result.report == report
    assert len(result.chunks) == 3
    assert result.chunks[0].content == "Reporting Agency: SFPD"
    assert result.chunks[0].spans[0].offset == 0
    assert result.chunks[0].spans[0].length == 22
    assert result.chunks[0].regions[0].page == 0
    # Polygon normalized by page width (8.5) and height (11.0).
    assert result.chunks[0].regions[0].points == [
        (0.0, 0.0),
        (0.5, 0.0),
        (0.5, 0.5 / 11.0),
        (0.0, 0.5 / 11.0),
    ]
    # Second paragraph spans the full page width.
    assert result.chunks[1].regions[0].points == [
        (0.0, 1.0 / 11.0),
        (1.0, 1.0 / 11.0),
        (1.0, 1.5 / 11.0),
        (0.0, 1.5 / 11.0),
    ]
    # Third paragraph is on page index 1.
    assert result.chunks[2].regions[0].page == 1

    client.responses.parse.assert_called_once()
    call_kwargs = client.responses.parse.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o-2024-05-13"
    assert call_kwargs["store"] is False
    assert call_kwargs["text_format"] is PoliceReport
    assert call_kwargs["input"] == [
        {"role": "system", "content": "Extract the ontology."},
        {
            "role": "user",
            "content": [
                ResponseInputText.model_validate(
                    {
                        "type": "input_text",
                        "text": (
                            "XML DOCUMENT\n===\n"
                            "<CONTENT>"
                            '<P id="0">Reporting Agency: SFPD</P>'
                            '<P id="1">Incident: Theft at 101 Main St</P>'
                            '<P id="2">Narrative paragraph on page 2.</P>'
                            "</CONTENT>"
                        ),
                    }
                )
            ],
        },
    ]


@patch("bc2.core.common.openai.OpenAI")
def test_driver_call_persists_ontology_in_context(openai_mock):
    report = _make_report()
    _install_openai_mock(openai_mock, report)

    cfg = _make_config()

    file = MemoryFile(
        content=json.dumps(_analyze_result_dict()).encode("utf-8"),
        mime_type="application/x-analyze-result",
    )
    context = Context()

    output = cfg.driver(file, context)

    assert output.mime_type == "application/x-ontology"
    assert context.ontology is not None
    assert context.ontology.report == report
    assert len(context.ontology.chunks) == 3

    serialized = json.loads(output.content().decode("utf-8"))
    assert serialized["report"]["case_number"]["content"] == "2024-0001"
    assert len(serialized["chunks"]) == 3


@patch("bc2.core.common.openai.OpenAI")
def test_extract_raises_when_parsed_is_none(openai_mock):
    _install_openai_mock(openai_mock, None)

    cfg = _make_config()

    analyze_result = AnalyzeResult(_analyze_result_dict())

    with pytest.raises(ValueError, match="no structured output"):
        cfg.driver.extract(analyze_result)


@patch("bc2.core.common.openai.OpenAI")
def test_driver_raises_empty_ontology_when_no_paragraphs(openai_mock):
    report = _make_report()
    _install_openai_mock(openai_mock, report)

    cfg = _make_config()

    file = MemoryFile(
        content=json.dumps({"paragraphs": [], "pages": []}).encode("utf-8"),
        mime_type="application/x-analyze-result",
    )

    with pytest.raises(EmptyOntologyError):
        cfg.driver(file, Context())


@patch("bc2.core.common.openai.OpenAI")
def test_extract_raises_when_bounding_page_missing(openai_mock):
    report = _make_report()
    _install_openai_mock(openai_mock, report)

    cfg = _make_config()

    from azure.ai.documentintelligence.models import AnalyzeResult

    analyze_result = AnalyzeResult(
        {
            "paragraphs": [
                {
                    "content": "Stray paragraph",
                    "spans": [{"offset": 0, "length": 15}],
                    "boundingRegions": [
                        {
                            "pageNumber": 99,
                            "polygon": [0, 0, 1, 0, 1, 1, 0, 1],
                        }
                    ],
                }
            ],
            "pages": [{"pageNumber": 1, "width": 8.5, "height": 11.0}],
        }
    )

    with pytest.raises(ValueError, match="Page 99 not found"):
        cfg.driver.extract(analyze_result)
