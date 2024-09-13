import io
from abc import ABC, abstractmethod
from typing import Literal

from ..common.file import MemoryFile


class BaseOutputDriver(ABC):
    """An output driver writes data from memory to some destination.

    Optionally, the path parameter can be used to specify a file path or URL.

    The path is only relevant for some output drivers; others (like stdout)
    will ignore it.

    The output driver must have side effects, such as writing to a file.
    The input arguments of either a `path` or a `buffer` can specify where
    the side effect will take place. These arguments will be interpreted
    differently depending on the output driver.

    The output driver should return `None`.
    """

    required: list[Literal["path"] | Literal["buffer"]] = []

    @abstractmethod
    def __call__(
        self, file: MemoryFile, path: str = "", buffer: io.BytesIO | None = None
    ) -> None: ...
