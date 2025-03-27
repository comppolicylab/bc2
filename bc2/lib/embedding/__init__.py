from typing import Union

from .embedding import Embedding
from .openai import OpenAIEmbeddingConfig

EmbeddingConfig = Union[OpenAIEmbeddingConfig]

__all__ = ["Embedding", "EmbeddingConfig"]
