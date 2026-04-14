from abc import ABC, abstractmethod
from typing import Generic, Tuple, TypeVar

from ..common.file import MemoryFile
from ..common.preprocess import PreprocessMixin
from ..common.text import Text

T = TypeVar("T")


class EmptyExtractionError(Exception):
    """Raised when an extraction process fails to find any text."""

    pass


class BaseExtractDriver(ABC, Generic[T], PreprocessMixin[T]):
    def __call__(self, file: MemoryFile) -> Text:
        """Extract the narrative from the given file.

        Args:
            file (MemoryFile): The file to extract the text from.

        Returns:
            Text: The extracted text.

        Raises:
            EmptyExtractionError: When no text is found
            MissingPreprocessorError: When no preprocessor is found for the file
        """
        data = self.preprocess(file)
        text, is_truncated = self.extract(data)
        if not text:
            raise EmptyExtractionError("No text found in file.")
        return Text(text, truncated=is_truncated)

    @abstractmethod
    def extract(self, data: T) -> Tuple[str, bool]:
        """Extract the narrative from the given files.

        Args:
            data (T): The preprocessed input data

        Returns:
            Tuple[str, bool]: The extracted text and whether the output is truncated
        """
        ...
