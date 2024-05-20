from abc import ABC, abstractmethod

from ..common.file import MemoryFile


class BaseInputDriver(ABC):
    """An input driver reads data into memory from some source.

    Optionally, the path parameter can be used to specify a file path or URL.

    The path is only relevant for some input drivers; others (like stdin)
    will ignore it.
    """

    @abstractmethod
    def __call__(self, path: str = "") -> MemoryFile: ...
