import io
from abc import ABC, abstractmethod
from typing import Literal

from ..common.context import Context
from ..common.file import MemoryFile


class BaseInputDriver(ABC):
    """An input driver reads data into memory from some source.

    Optionally, the path parameter can be used to specify a file path or URL.

    The path is only relevant for some input drivers; others (like stdin)
    will ignore it.
    """

    required: list[Literal["path"] | Literal["buffer"]] = []

    def __call__(
        self, context: Context, path: str = "", buffer: io.BytesIO | None = None
    ) -> MemoryFile:
        """Load a file from a path or buffer."""
        f = self.load_file(path=path, buffer=buffer)
        context.input_file = f
        return f

    @abstractmethod
    def load_file(
        self, path: str = "", buffer: io.BytesIO | None = None
    ) -> MemoryFile: ...
