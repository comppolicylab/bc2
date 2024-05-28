from abc import ABC, abstractmethod

from ..common.text import Text


class BaseParseDriver(ABC):
    @abstractmethod
    def __call__(self, narrative: Text) -> Text: ...
