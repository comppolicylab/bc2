from abc import ABC, abstractmethod

from ..common.text import RedactedText, Text


class BaseRedactDriver(ABC):
    @abstractmethod
    def __call__(self, narrative: Text) -> RedactedText: ...
