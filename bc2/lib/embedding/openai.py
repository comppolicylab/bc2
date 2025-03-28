from functools import cached_property

from openai import AsyncOpenAI, AzureOpenAI, OpenAI
from openai.types import CreateEmbeddingResponse
from pydantic import BaseModel

from bc2.core.common.openai import OpenAIClientConfig

from .base import BaseEmbeddingDriver
from .embedding import Embedding


class OpenAIEmbeddingGeneratorConfig(BaseModel):
    """Configuration for the model used for generating embeddings."""

    model: str
    dimensions: int | None = None
    model_version: str = ""


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
        result = self.client.embeddings.create(input=text, model=self.config.model)
        return self._format_result(result)

    async def embed_async(self, text: str) -> Embedding:
        result = await self.aclient.embeddings.create(
            input=text, model=self.config.model
        )
        return self._format_result(result)

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
