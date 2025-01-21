from abc import ABC, abstractmethod

from ..common.context import Context
from ..common.text import Text


class BaseParseDriver(ABC):
    @abstractmethod
    def __call__(self, text: Text, context: Context) -> Text: ...
