from abc import ABC, abstractmethod

from ..common.text import Text


class BaseRedactDriver(ABC):
    @abstractmethod
    def __call__(self, narrative: Text) -> Text: ...
