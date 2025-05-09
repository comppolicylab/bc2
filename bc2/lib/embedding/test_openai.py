import pytest

from bc2.core.common.openai import OpenAIClientConfig
from bc2.core.common.openai_metadata import get_encoding_for_model

from .openai import OpenAIEmbeddingConfig, OpenAIEmbeddingGeneratorConfig


@pytest.mark.parametrize(
    "model,text,trimmed",
    [
        ("text-embedding-3-large", "a " * 1, "a " * 1),
        ("text-embedding-3-large", "a " * 10, "a " * 10),
        ("text-embedding-3-large", "a " * 100, "a " * 100),
        ("text-embedding-3-large", "a " * 1_000, "a " * 1_000),
        ("text-embedding-3-large", "a " * 10_000, ("a " * 8_192)[:-1]),
    ],
    ids=[
        "1 token",
        "10 tokens",
        "100 tokens",
        "1_000 tokens",
        "10_000 tokens",
    ],
)
def test_trim_input(model: str, text: str, trimmed: str):
    embed = OpenAIEmbeddingConfig(
        client=OpenAIClientConfig(api_key="test"),
        generator=OpenAIEmbeddingGeneratorConfig(model=model),
    )

    encoding = get_encoding_for_model(model)

    assert embed.driver._trim_input(text) == trimmed
    assert len(encoding.encode(trimmed)) <= embed.generator.max_input_tokens
