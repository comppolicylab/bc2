import logging
import re
from abc import ABC, abstractmethod
from typing import Callable, Generic, TypeVar, cast

from ..common.file import MemoryFile
from ..common.text import Text

logger = logging.getLogger(__name__)

T = TypeVar("T")


class EmptyExtractionError(Exception):
    """Raised when an extraction process fails to find any text."""

    pass


class MissingPreprocessorError(Exception):
    """Raised when no preprocessor is found for the given file type."""

    pass


class Preprocessor(ABC, Generic[T]):
    mime_type: re.Pattern

    @abstractmethod
    def __call__(self, file: MemoryFile) -> T: ...

    @abstractmethod
    def __name__(self) -> str: ...


def register_preprocessor(mime: str):
    """Decorator to set the mime type of the processor."""

    def decorator(func: Callable[[MemoryFile], T]) -> Preprocessor[T]:
        preprocessor = cast(Preprocessor[T], func)
        preprocessor.mime_type = re.compile(mime)
        return preprocessor

    return decorator


class BaseExtractDriver(ABC, Generic[T]):
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
        text = self.extract(data)
        if not text:
            raise EmptyExtractionError("No text found in file.")
        return Text(text)

    def preprocess(self, file: MemoryFile) -> T:
        """Preprocess the file before extraction.

        Args:
            file (MemoryFile): The file to preprocess.

        Returns:
            T - Intermediate data for extraction
        """
        # Look through available methods to find a matching mime type
        for method in dir(self):
            fn = getattr(self, method)
            if not hasattr(fn, "mime_type"):
                continue
            preprocessor = cast(Preprocessor[T], fn)
            pattern = preprocessor.mime_type
            if pattern.match(file.mime_type):
                logger.debug(
                    "Using preprocessor '%s' for file type '%s'",
                    preprocessor.__name__,
                    file.mime_type,
                )
                return preprocessor(file)
        raise MissingPreprocessorError(
            f"Missing preprocessor for type '{file.mime_type}'"
        )

    @abstractmethod
    def extract(self, data: T) -> str:
        """Extract the narrative from the given files.

        Args:
            data (T): The preprocessed input data

        Returns:
            str: The extracted text.
        """
        ...
