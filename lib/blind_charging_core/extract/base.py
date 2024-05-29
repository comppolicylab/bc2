from abc import ABC, abstractmethod

from ..common.file import MemoryFile
from ..common.text import Text


class EmptyExtractionError(Exception):
    """Raised when an extraction process fails to find any text."""

    pass


class BaseExtractDriver(ABC):
    @abstractmethod
    def __call__(self, file: MemoryFile) -> Text:
        """Extract the narrative from the given file.

        Args:
            file (MemoryFile): The file to extract the text from.

        Returns:
            Text: The extracted text.

        Raises:
            EmptyExtractionError: When no text is found
        """
        ...
