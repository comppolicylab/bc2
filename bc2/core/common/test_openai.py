import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from .openai import (
    FilteredContentError,
    OpenAIChatConfig,
    OpenAIChatInputText,
    OpenAIChatOutput,
    OpenAIChatPromptBuiltIn,
    OpenAIChatPromptFile,
    OpenAIChatPromptInline,
    OpenAIChatTurn,
    OpenAIClientConfig,
    _openai_provider,
)
from .usage import create_usage_tracker, usage_operation, usage_tracking


@pytest.mark.parametrize(
    "base_url",
    [
        "https://example.openai.azure.com/",
        "https://example.openai.azure.us/",
    ],
)
def test_openai_provider_recognizes_azure_clouds(base_url):
    client = MagicMock()
    client.base_url = base_url

    assert _openai_provider(client) == "azure"


def test_fix_azure_endpoint():
    cfg = OpenAIClientConfig(
        api_key="my-api-key",
        azure_endpoint="https://my-azure-endpoint.com/",
        api_version="2024-11-30",
    )
    assert cfg.azure_endpoint == "https://my-azure-endpoint.com/"
    client = cfg.init()
    assert client.base_url == "https://my-azure-endpoint.com/openai/v1/"


def test_chat_prompt_builtin_serialize():
    c = OpenAIChatPromptBuiltIn(prompt_id="redact")
    d = c.model_dump()
    assert d == {
        "engine": "string",
        "prompt_id": c.prompt_id,
        "examples_id": c.examples_id,
    }
    d2 = c.model_dump(context={"freeze": True})
    assert d2 == {
        "engine": "string",
        "prompt": c.prompt_value,
        "examples": c.examples_value,
    }
    d3 = c.model_dump(exclude_none=True)
    assert d3 == {
        "engine": "string",
        "prompt_id": c.prompt_id,
    }
    d4 = c.model_dump(context={"freeze": True}, exclude_none=True)
    assert d4 == {
        "engine": "string",
        "prompt": c.prompt_value,
        "examples": [],
    }


def test_chat_prompt_inline_serialize():
    c = OpenAIChatPromptInline(prompt="Hello, {alias}!", engine="string")
    d = c.model_dump()
    assert d == {
        "engine": "string",
        "prompt": c.prompt,
        "examples": c.examples,
    }
    d2 = c.model_dump(context={"freeze": True})
    assert d2 == {
        "engine": "string",
        "prompt": c.prompt,
        "examples": c.examples,
    }


def test_chat_prompt_file_serialize():
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write("Hello, {alias}!")
        f.flush()
        c = OpenAIChatPromptFile(prompt_file=f.name, engine="string")
        d = c.model_dump()
        assert d == {
            "engine": "string",
            "prompt_file": c.prompt_file,
            "examples_file": c.examples_file,
        }
        d2 = c.model_dump(context={"freeze": True})
        assert d2 == {
            "engine": "string",
            "prompt": c.prompt_value,
            "examples": c.examples_value,
        }


def test_chat_prompt_builtin():
    c = OpenAIChatPromptBuiltIn(prompt_id="redact")
    # Real file is in ../../../data/prompts/redact.txt
    cur_dur = Path(__file__).parent
    assert (
        c.prompt_value
        == (cur_dur / "../../data/prompts/redact.txt").resolve().read_text()
    )


def test_format_prompt_inline_jinja():
    c = OpenAIChatPromptInline(prompt="Hello, {{ alias }}!", engine="jinja")
    assert c.format("How are you?", alias="world") == [
        OpenAIChatTurn(
            role="system",
            content="Hello, world!",
        ),
        OpenAIChatTurn(
            role="user",
            content=[OpenAIChatInputText(text="How are you?", type="text")],
        ),
    ]


def test_format_prompt_inline_string():
    c = OpenAIChatPromptInline(prompt="Hello, {alias}!", engine="string")
    assert c.format("How are you?", alias="world") == [
        OpenAIChatTurn(
            role="system",
            content="Hello, world!",
        ),
        OpenAIChatTurn(
            role="user",
            content=[OpenAIChatInputText(text="How are you?", type="text")],
        ),
    ]


def test_format_prompt_inline_string_no_placeholder():
    c = OpenAIChatPromptInline(prompt="Hello!", engine="string")
    assert c.format("How are you?", alias="world") == [
        OpenAIChatTurn(
            role="system",
            content="Hello!\nworld",
        ),
        OpenAIChatTurn(
            role="user",
            content=[OpenAIChatInputText(text="How are you?", type="text")],
        ),
    ]


def test_format_prompt_file_jinja():
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write("Hello, {{ alias }}!")
        f.flush()
        c = OpenAIChatPromptFile(prompt_file=f.name, engine="jinja")
        assert c.format("How are you?", alias="world") == [
            OpenAIChatTurn(
                role="system",
                content="Hello, world!",
            ),
            OpenAIChatTurn(
                role="user",
                content=[OpenAIChatInputText(text="How are you?", type="text")],
            ),
        ]


def test_format_prompt_file_string():
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write("Hello, {alias}!")
        f.flush()
        c = OpenAIChatPromptFile(prompt_file=f.name, engine="string")
        assert c.format("How are you?", alias="world") == [
            OpenAIChatTurn(
                role="system",
                content="Hello, world!",
            ),
            OpenAIChatTurn(
                role="user",
                content=[OpenAIChatInputText(text="How are you?", type="text")],
            ),
        ]


def test_format_prompt_file_string_no_placeholder():
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write("Hello!")
        f.flush()
        c = OpenAIChatPromptFile(prompt_file=f.name, engine="string")
        assert c.format("How are you?", alias="world") == [
            OpenAIChatTurn(
                role="system",
                content="Hello!\nworld",
            ),
            OpenAIChatTurn(
                role="user",
                content=[OpenAIChatInputText(text="How are you?", type="text")],
            ),
        ]


def _build_chat_config(max_tokens: int = 100) -> OpenAIChatConfig:
    return OpenAIChatConfig.model_validate(
        {
            "method": "chat",
            "model": "gpt-4.1-2025-04-14",
            "max_tokens": max_tokens,
            "system": {
                "engine": "string",
                "prompt": "Be concise.",
            },
        }
    )


def _mock_response(
    *,
    status: str,
    output_text: str,
    output_tokens: int,
    incomplete_reason: str | None = None,
) -> MagicMock:
    response = MagicMock()
    response.status = status
    response.output_text = output_text
    response.usage = type(
        "Usage",
        (),
        {
            "input_tokens": 20,
            "output_tokens": output_tokens,
            "total_tokens": 20 + output_tokens,
            "input_tokens_details": type("InputDetails", (), {"cached_tokens": 5})(),
            "output_tokens_details": type(
                "OutputDetails", (), {"reasoning_tokens": 3}
            )(),
        },
    )()
    response.id = "resp_test"
    response.model = "gpt-4.1-2025-04-14"
    if incomplete_reason is None:
        response.incomplete_details = None
    else:
        response.incomplete_details = type(
            "IncompleteDetails", (), {"reason": incomplete_reason}
        )()
    response.output_parsed = None
    response.error = None
    return response


def test_invoke_returns_truncated_output_on_max_output_tokens():
    """A response that hits `max_output_tokens` should not raise.

    The chunker relies on getting back a truncated `OpenAIChatOutput` so it
    can resume processing on the remainder. This test guards against a
    regression where the Responses API integration raised instead.
    """
    cfg = _build_chat_config(max_tokens=100)
    client = MagicMock()
    client.responses.create.return_value = _mock_response(
        status="incomplete",
        output_text="partial answer ...",
        output_tokens=100,
        incomplete_reason="max_output_tokens",
    )

    result = cfg.invoke(client, "go")

    assert result.content == "partial answer ..."
    assert result.truncated is True
    assert result.is_truncated is True
    assert result.max_tokens == 100
    assert result.completion_tokens == 100


def test_invoke_raises_filtered_content_error():
    cfg = _build_chat_config()
    client = MagicMock()
    client.responses.create.return_value = _mock_response(
        status="incomplete",
        output_text="",
        output_tokens=0,
        incomplete_reason="content_filter",
    )

    with pytest.raises(FilteredContentError):
        cfg.invoke(client, "go")


def test_invoke_raises_on_unexpected_incomplete_status():
    cfg = _build_chat_config()
    client = MagicMock()
    client.responses.create.return_value = _mock_response(
        status="failed",
        output_text="",
        output_tokens=0,
        incomplete_reason=None,
    )

    with pytest.raises(ValueError, match="not completed"):
        cfg.invoke(client, "go")


def test_invoke_completed_response_is_not_truncated():
    cfg = _build_chat_config(max_tokens=100)
    client = MagicMock()
    client.responses.create.return_value = _mock_response(
        status="completed",
        output_text="full answer",
        output_tokens=42,
    )

    result = cfg.invoke(client, "go")

    assert result.content == "full answer"
    assert result.truncated is False
    assert result.is_truncated is False


def test_invoke_records_response_usage():
    cfg = _build_chat_config()
    client = MagicMock()
    client.base_url = "https://example.openai.azure.com/openai/v1/"
    client.responses.create.return_value = _mock_response(
        status="completed",
        output_text="full answer",
        output_tokens=42,
    )
    created = create_usage_tracker({"report_usage": True})
    assert created is not None
    report, tracker = created

    with usage_tracking(tracker), usage_operation("parse:openai"):
        cfg.invoke(client, "go")

    call = report["calls"][0]
    assert call["provider"] == "azure"
    assert call["service"] == "responses"
    assert call["operation"] == "parse:openai"
    assert call["response_id"] == "resp_test"
    assert call["usage"] == {
        "input_tokens": 20,
        "output_tokens": 42,
        "total_tokens": 62,
        "cached_input_tokens": 5,
        "reasoning_output_tokens": 3,
    }


def test_chat_output_is_truncated_inferred_from_token_match():
    """When the API doesn't surface a stop reason but we used every token,
    we still report the output as truncated."""
    output = OpenAIChatOutput[str](
        content="full",
        completion_tokens=100,
        max_tokens=100,
    )
    assert output.truncated is False
    assert output.is_truncated is True


def test_chat_output_is_truncated_explicit_flag_wins():
    """An explicit truncated flag should win even if tokens don't match."""
    output = OpenAIChatOutput[str](
        content="partial",
        completion_tokens=42,
        max_tokens=100,
        truncated=True,
    )
    assert output.is_truncated is True
