from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..common.context import Context
from ..common.file import MemoryFile
from ..common.preprocess import PreprocessMixin

T = TypeVar("T")


class BasePainter(ABC, Generic[T], PreprocessMixin[T]):
    def __call__(self, file: MemoryFile, context: Context) -> MemoryFile:
        """Paint a file, returning an annotated version.

        `file` is the primary pipe value (e.g. a serialized ontology result).
        The original input file is read from `context.input_file`.
        """
        data = self.preprocess(file)
        return self.paint(context.input_file, data)

    @abstractmethod
    def paint(self, original: MemoryFile, data: T) -> MemoryFile:
        """Paint the input file using current analysis."""
        ...
