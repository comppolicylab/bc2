from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..common.context import Context
from ..common.file import MemoryFile
from ..common.preprocess import PreprocessMixin

T = TypeVar("T")


class BasePainter(ABC, Generic[T], PreprocessMixin[T]):
    def __call__(self, file: MemoryFile, context: Context) -> MemoryFile:
        """Paint a file, returning an annotated version."""
        current = self.preprocess(file)
        return self.paint(context.input_file, current)

    @abstractmethod
    def paint(self, original: MemoryFile, data: T) -> MemoryFile:
        """Paint the preprocessed input, returning an annotated MemoryFile."""
        ...
