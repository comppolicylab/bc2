import tempfile
from pathlib import Path

from .openai import (
    OpenAIChatInputText,
    OpenAIChatPromptBuiltIn,
    OpenAIChatPromptFile,
    OpenAIChatPromptInline,
    OpenAIChatTurn,
    OpenAIClientConfig,
)


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
