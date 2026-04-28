from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import AsyncOpenAI, OpenAI

from bc2.core.common.openai import OpenAIClientConfig
from bc2.core.common.openai_metadata import get_encoding_for_model

from .openai import (
    OpenAIEmbeddingConfig,
    OpenAIEmbeddingDriver,
    OpenAIEmbeddingGeneratorConfig,
)


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


def _mock_embedding_response(model: str = "text-embedding-3-large") -> MagicMock:
    response = MagicMock()
    response.data = [MagicMock(embedding=[0.0, 0.1, 0.2])]
    response.model = model
    return response


@pytest.mark.parametrize(
    "dimensions",
    [None, 256, 1024],
    ids=["unset", "256", "1024"],
)
def test_embed_passes_dimensions(dimensions: int | None):
    client = MagicMock(spec=OpenAI)
    client.embeddings.create.return_value = _mock_embedding_response()
    aclient = MagicMock(spec=AsyncOpenAI)

    config = OpenAIEmbeddingGeneratorConfig(
        model="text-embedding-3-large",
        dimensions=dimensions,
    )
    driver = OpenAIEmbeddingDriver(client, aclient, config)

    driver.embed("hello")

    client.embeddings.create.assert_called_once()
    call_kwargs = client.embeddings.create.call_args.kwargs
    assert call_kwargs["input"] == "hello"
    assert call_kwargs["model"] == "text-embedding-3-large"
    if dimensions is None:
        assert "dimensions" not in call_kwargs
    else:
        assert call_kwargs["dimensions"] == dimensions


def test_embed_config_dimensions_default():
    config = OpenAIEmbeddingConfig(
        client=OpenAIClientConfig(api_key="test"),
        generator=OpenAIEmbeddingGeneratorConfig(model="text-embedding-3-large"),
    )
    assert config.generator.dimensions is None


def test_embed_config_dimensions_override():
    config = OpenAIEmbeddingConfig(
        client=OpenAIClientConfig(api_key="test"),
        generator=OpenAIEmbeddingGeneratorConfig(
            model="text-embedding-3-large", dimensions=512
        ),
    )
    assert config.generator.dimensions == 512
    assert config.generator.model_dimensions == 512


@pytest.mark.asyncio
async def test_embed_async_passes_dimensions():
    client = MagicMock(spec=OpenAI)
    aclient = MagicMock(spec=AsyncOpenAI)
    aclient.embeddings.create = AsyncMock(return_value=_mock_embedding_response())

    config = OpenAIEmbeddingGeneratorConfig(
        model="text-embedding-3-large",
        dimensions=512,
    )
    driver = OpenAIEmbeddingDriver(client, aclient, config)
    await driver.embed_async("hello")
    aclient.embeddings.create.assert_awaited_once()
    call_kwargs = aclient.embeddings.create.call_args.kwargs
    assert call_kwargs["input"] == "hello"
    assert call_kwargs["model"] == "text-embedding-3-large"
    assert call_kwargs["dimensions"] == 512
