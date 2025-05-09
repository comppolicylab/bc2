import logging
from functools import cached_property

import tiktoken
from openai import AsyncOpenAI, AzureOpenAI, OpenAI
from openai.types import CreateEmbeddingResponse
from pydantic import BaseModel, Field, PositiveInt

from bc2.core.common.openai import OpenAIClientConfig
from bc2.core.common.openai_metadata import (
    EmbeddingModelMeta,
    ModelNotFound,
    get_embedding_model_meta,
    get_encoding_for_model,
)

from .base import BaseEmbeddingDriver
from .embedding import Embedding

logger = logging.getLogger(__name__)


_DEFAULT_MAX_INPUT_TOKENS = 8191  # Default max tokens for OpenAI embedding models


class OpenAIEmbeddingGeneratorConfig(BaseModel):
    """Configuration for the model used for generating embeddings."""

    model: str
    openai_model: str | None = Field(
        None,
        description=(
            "When using Azure, the `model` refers to a model *deployment*. "
            "Set the `openai_model` parameter to indicate which "
            "underlying OpenAI model is used."
        ),
    )
    max_tokens: PositiveInt | None = None
    dimensions: PositiveInt | None = None
    model_version: str = ""

    @property
    def model_meta(self) -> EmbeddingModelMeta | None:
        """Get the completion tokens for the model."""
        model_name = self.openai_model or self.model
        try:
            return get_embedding_model_meta(model_name)
        except ModelNotFound:
            logger.warning(f"Model '{model_name}' not found in metadata.")
            return None

    @property
    def max_input_tokens(self) -> int:
        """Get the max input tokens for the model."""
        if self.max_tokens is not None:
            return self.max_tokens
        model_meta = self.model_meta
        if model_meta:
            return model_meta.max_input_tokens
        return _DEFAULT_MAX_INPUT_TOKENS

    @property
    def encoding(self) -> tiktoken.Encoding:
        """Get the encoding to use for the model."""
        model_name = self.openai_model or self.model
        return get_encoding_for_model(model_name)


class OpenAIEmbeddingConfig(BaseModel):
    """Configuration for the OpenAI (or Azure OpenAI) embedding driver."""

    client: OpenAIClientConfig
    generator: OpenAIEmbeddingGeneratorConfig

    @cached_property
    def driver(self) -> "OpenAIEmbeddingDriver":
        client = self.client.init()
        aclient = self.client.init_async()
        return OpenAIEmbeddingDriver(client, aclient, self.generator)


class OpenAIEmbeddingDriver(BaseEmbeddingDriver):
    def __init__(
        self,
        client: OpenAI,
        aclient: AsyncOpenAI,
        config: OpenAIEmbeddingGeneratorConfig,
    ) -> None:
        self.config = config
        self.client = client
        self.aclient = aclient

    def embed(self, text: str) -> Embedding:
        text = self._trim_input(text)
        result = self.client.embeddings.create(input=text, model=self.config.model)
        return self._format_result(result)

    async def embed_async(self, text: str) -> Embedding:
        text = self._trim_input(text)
        result = await self.aclient.embeddings.create(
            input=text, model=self.config.model
        )
        return self._format_result(result)

    def _trim_input(self, text: str) -> str:
        """Trim the input text to fit within the model's max input tokens.

        Args:
            text (str): The input text.

        Returns:
            str: The trimmed input text.
        """
        encoding = self.config.encoding
        max_tokens = self.config.max_input_tokens

        tokens = encoding.encode(text)
        n = len(tokens)
        if n > max_tokens:
            logger.debug(f"Trimming embedding input from {n} to {max_tokens} tokens")
            tokens = tokens[:max_tokens]
            return encoding.decode(tokens)
        return text

    def _format_result(self, result: CreateEmbeddingResponse) -> Embedding:
        """Format the result into an Embedding instance.

        Args:
            result (CreateEmbeddingResponse): The response from the API.

        Returns:
            Embedding: The local embedding with metadata.
        """
        vendor_name = self.client.__class__.__name__
        version = self.config.model_version
        result_model = result.model
        # NOTE(jnu): Similar to the completions APIs, Azure is *silly* about how
        # it handles model names. You have to specify the Azure deployment names,
        # which is usually different from the actual model name (and may not be
        # very informative). Fortunately, we can detect what the underlying model
        # actually was from the response! So when we're using Azure, we will
        # stuff the inferred model name into the version field.
        # (The `model` field in this case will be the Azure deployment.)
        if isinstance(self.client, AzureOpenAI):
            version = result_model
            if self.config.model_version:
                version += f"@{self.config.model_version}"

        return Embedding(
            result.data[0].embedding,
            vendor=vendor_name,
            model=self.config.model,
            model_version=version,
        )
