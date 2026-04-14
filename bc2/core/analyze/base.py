from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..common.file import MemoryFile
from ..common.preprocess import PreprocessMixin

T = TypeVar("T")


class BaseAnalyzeDriver(ABC, Generic[T], PreprocessMixin[T]):
    def __call__(self, file: MemoryFile) -> MemoryFile:
        """Run analysis over the given input file.

        Args:
            file (MemoryFile): The file to analyze.

        Returns:
            MemoryFile: The analysis result.

        Raises:
            MissingPreprocessorError: When no preprocessor is found for the file.
        """
        data = self.preprocess(file)
        return self.analyze(data)

    @abstractmethod
    def analyze(self, data: T) -> MemoryFile:
        """Analyze preprocessed input and return a result file."""
        ...
