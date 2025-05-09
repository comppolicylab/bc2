import logging
from dataclasses import dataclass

import tiktoken

logger = logging.getLogger(__name__)


# Default token encoding to use for models when lookup fails.
_DEFAULT_ENCODING = "o200k_base"


@dataclass
class ModelMeta:
    name: str


@dataclass
class ChatModelMeta(ModelMeta):
    context: int
    output: int


@dataclass
class EmbeddingModelMeta(ModelMeta):
    dimensions: int
    name: str
    max_input_tokens: int


_MODELS = {
    meta.name.lower(): meta
    ##########################################################
    # NOTE(jnu): ADD NEW MODELS HERE AS WE SUPPORT THEM.
    ##########################################################
    for meta in [
        ChatModelMeta(name="gpt-4o-2024-05-13", context=128_000, output=4_096),
        ChatModelMeta(name="gpt-4o-2024-08-06", context=128_000, output=16_384),
        ChatModelMeta(name="gpt-4o-2024-11-20", context=128_000, output=16_384),
        ChatModelMeta(name="o3-mini-2025-01-31", context=200_000, output=100_000),
        ChatModelMeta(name="o1-mini-2024-09-12", context=128_000, output=65_536),
        ChatModelMeta(
            name="gpt-4.5-preview-2025-02-27", context=128_000, output=16_384
        ),
        ChatModelMeta(name="gpt-4o-mini-2024-07-18", context=128_000, output=16_384),
        ChatModelMeta(name="gpt-4-turbo-2024-04-09", context=128_000, output=4_096),
        ChatModelMeta(name="gpt-4-0125-preview", context=128_000, output=4_096),
        ChatModelMeta(name="gpt-4-0613", context=8_192, output=8_192),
        ChatModelMeta(name="gpt-4-0314", context=8_192, output=8_192),
        ChatModelMeta(name="gpt-3.5-turbo-0125", context=16_385, output=4_096),
        ChatModelMeta(name="gpt-3.5-turbo-1106", context=16_385, output=4_096),
        EmbeddingModelMeta(
            name="text-embedding-3-large", dimensions=3_072, max_input_tokens=8_192
        ),
    ]
}


class ModelNotFound(Exception):
    """Raised when a model is not found in the metadata."""

    pass


def get_chat_model_meta(model: str) -> ChatModelMeta:
    """Get metadata for a chat model by name.

    Args:
        model: The fully-specified name of the model (e.g. 'gpt-4o-2024-05-13').

    Returns:
        The metadata for the model.

    Raises:
        ModelNotFound: If the model is not found.
    """
    # NOTE(jnu): We could support fuzzy matching to pull metadata when a
    # specific version is unspecified. There is a risk that our metadata is
    # out of date in this case and that the real model that OpenAI/Azure will
    # use in this case has different properties (such as an expanded context).
    # It's better to just throw an error and remind us to update the metadata.
    try:
        info = _MODELS[model.lower()]
        if not isinstance(info, ChatModelMeta):
            raise ModelNotFound(f"Chat model {model} not found in metadata")
        return info
    except KeyError as e:
        raise ModelNotFound(f"Chat model {model} not found in metadata") from e


def get_embedding_model_meta(model: str) -> EmbeddingModelMeta:
    """Get metadata for an embedding model by name.

    Args:
        model: The fully-specified name of the model (e.g. 'text-embedding-3-large').

    Returns:
        The metadata for the embedding model.

    Raises:
        ModelNotFound: If the model is not found.
    """
    try:
        info = _MODELS[model.lower()]
        if not isinstance(info, EmbeddingModelMeta):
            raise ModelNotFound(f"Embedding model {model} not found in metadata")
        return info
    except KeyError as e:
        raise ModelNotFound(f"Embedding model {model} not found in metadata") from e


def get_encoding_for_model(model: str) -> tiktoken.Encoding:
    """Get the token encoding for a model.

    Args:
        model: The name of the model.

    Returns:
        The encoding for the model.
    """
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        logger.warning(
            f"Using default tokenizer {_DEFAULT_ENCODING} for "
            f"{model} since true encoding is unknown"
        )
        return tiktoken.get_encoding(_DEFAULT_ENCODING)
