import tempfile
from pathlib import Path

from .openai import (
    OpenAIChatInputText,
    OpenAIChatPromptBuiltIn,
    OpenAIChatPromptFile,
    OpenAIChatPromptInline,
    OpenAIChatTurn,
)


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
