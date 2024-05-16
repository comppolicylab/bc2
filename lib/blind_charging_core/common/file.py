import tempfile
from contextlib import contextmanager
from typing import Iterable


class Memoryfile:
    def __init__(self, file: bytes):
        self.bytes = file

    @contextmanager
    def materialize(self) -> Iterable[str]:
        with tempfile.NamedTemporaryFile(delete_on_close=False) as f:
            f.write(self.bytes)
            f.close()
            yield f.name
