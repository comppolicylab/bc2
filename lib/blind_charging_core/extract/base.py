from abc import ABC, abstractmethod

from ..common.file import MemoryFile
from ..common.text import Text


class EmptyExtractionError(Exception):
    """Raised when an extraction process fails to find a narrative."""

    pass


class BaseExtractDriver(ABC):
    @abstractmethod
    def __call__(self, file: MemoryFile) -> Text:
        """Extract the narrative from the given file.

        Args:
            file (MemoryFile): The file to extract the narrative from.

        Returns:
            Text: The extracted narrative.

        Raises:
            EmptyExtractionError: When no narrative is found
        """
        ...
