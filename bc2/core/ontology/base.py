from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..common.file import MemoryFile
from ..common.ontology import PoliceReportParseResult
from ..common.preprocess import PreprocessMixin

T = TypeVar("T")


class EmptyOntologyError(Exception):
    """Raised when ontology extraction returns an empty result."""

    pass


class BaseOntologyDriver(ABC, Generic[T], PreprocessMixin[T]):
    def __call__(self, file: MemoryFile) -> MemoryFile:
        """Extract a structured police report ontology from a file."""
        data = self.preprocess(file)
        result = self.extract(data)
        if not result.chunks:
            raise EmptyOntologyError(
                "No source chunks found in ontology extraction result."
            )

        # Serialize for transport.
        f = MemoryFile(
            content=result.model_dump_json().encode("utf-8"),
            mime_type="application/x-ontology",
        )
        return f

    @abstractmethod
    def extract(self, data: T) -> PoliceReportParseResult:
        """Extract a police report ontology from preprocessed input."""
        ...
