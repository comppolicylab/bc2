from abc import ABC, abstractmethod

from .embedding import Embedding


class BaseEmbeddingDriver(ABC):
    @abstractmethod
    def embed(self, text: str) -> Embedding: ...

    @abstractmethod
    async def embed_async(self, text: str) -> Embedding: ...
