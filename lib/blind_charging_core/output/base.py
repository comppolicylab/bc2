import io
from abc import ABC, abstractmethod

from ..common.file import MemoryFile


class BaseOutputDriver(ABC):
    """An output driver writes data from memory to some destination.

    Optionally, the path parameter can be used to specify a file path or URL.

    The path is only relevant for some output drivers; others (like stdout)
    will ignore it.

    The output driver can return a BytesIO object if the output is in-memory.
    In other cases the driver will have IO side effects (like writing to a file),
    and return None.
    """

    required: list[str] = []

    @abstractmethod
    def __call__(
        self, file: MemoryFile, output_path: str = ""
    ) -> io.BytesIO | None: ...
