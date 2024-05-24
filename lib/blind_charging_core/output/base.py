from abc import ABC, abstractmethod

from ..common.file import MemoryFile


class BaseOutputDriver(ABC):
    """An output driver writes data from memory to some destination.

    Optionally, the path parameter can be used to specify a file path or URL.

    The path is only relevant for some output drivers; others (like stdout)
    will ignore it.
    """

    required: list[str] = []

    @abstractmethod
    def __call__(self, file: MemoryFile, output_path: str = "") -> None: ...
