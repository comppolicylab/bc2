from .codec import EmbeddingCodec


class Embedding(EmbeddingCodec):
    def __init__(
        self,
        vector: list[float] | tuple[float],
        vendor: str = "",
        model: str = "",
        model_version: str = "",
    ) -> None:
        """Initialize the embedding with a vector."""
        super().__init__(vector)

        self.vendor = vendor
        self.model = model
        self.model_version = model_version

    def __repr__(self) -> str:
        # Take up to 3 items from the vector for the representation.
        vector_repr = ""
        if self.dimensions > 3:
            vector_repr = ", ".join(str(v) for v in self.vector[:3]) + ", ..."
        else:
            vector_repr = ", ".join(str(v) for v in self.vector)
        return f"<Embedding:{self.dimensions} ({vector_repr})>"

    def __str__(self) -> str:
        return self.to_base64()

    def __bytes__(self) -> bytes:
        return self.to_binary()

    @property
    def dimensions(self) -> int:
        """Return the number of dimensions in the embedding."""
        return len(self.vector)
