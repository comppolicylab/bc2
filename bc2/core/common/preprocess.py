import logging
import re
from abc import ABC, abstractmethod
from typing import Callable, Generic, TypeVar, cast

from .file import MemoryFile

logger = logging.getLogger(__name__)


TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
TPreprocessed = TypeVar("TPreprocessed")


class MissingPreprocessorError(Exception):
    """Raised when no preprocessor is found for the given file type."""

    pass


class Preprocessor(ABC, Generic[TInput, TOutput]):
    mime_type: re.Pattern

    @abstractmethod
    def __call__(self, file: TInput) -> TOutput: ...

    @abstractmethod
    def __name__(self) -> str: ...


class PreprocessMixin(Generic[TPreprocessed]):
    def preprocess(self, file: MemoryFile) -> TPreprocessed:
        """Preprocess a file before processing."""
        # Look through available methods to find a matching mime type.
        for method in dir(self):
            fn = getattr(self, method)
            if not hasattr(fn, "mime_type"):
                continue
            preprocessor = cast(Preprocessor[MemoryFile, TPreprocessed], fn)
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


def register_preprocessor(mime: str):
    """Decorator to set the mime type of the processor."""

    def decorator(func: Callable[[TInput], TOutput]) -> Preprocessor[TInput, TOutput]:
        preprocessor = cast(Preprocessor[TInput, TOutput], func)
        preprocessor.mime_type = re.compile(mime)
        return preprocessor

    return decorator
