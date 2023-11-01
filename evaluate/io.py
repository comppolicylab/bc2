import os
from abc import abstractmethod
from typing import Protocol


class FileReader(Protocol):
    """Read files from somewhere."""

    @abstractmethod
    def read(self, name: str) -> str:
        raise NotImplementedError


class LocalFileReader(FileReader):
    """Read files from the local filesystem."""

    def __init__(self, root: str = "."):
        self._root = root

    def read(self, name: str) -> str:
        fp = os.path.join(self._root, name)
        with open(fp) as f:
            return f.read()
