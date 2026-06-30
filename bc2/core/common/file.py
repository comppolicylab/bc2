import base64
import shutil
from functools import cached_property
from io import SEEK_END, BytesIO
from typing import IO

import magic


class MemoryFile:
    def __init__(self, content: bytes = b"", mime_type: str | None = None):
        self.buffer = BytesIO(content)
        self._explicit_mime_type = mime_type

    def content(self):
        return self.buffer.getvalue()

    def view(self) -> memoryview:
        """Return a zero-copy read-only view of the buffer contents.

        Unlike `content()`, this does not copy the underlying bytes. The
        returned `memoryview` keeps the buffer locked against resizing for as
        long as it is alive, so callers must release it (let it go out of
        scope) before writing to the buffer again.
        """
        return self.buffer.getbuffer()

    def write(self, content: str, encoding: str = "utf-8") -> None:
        self.buffer.seek(0, SEEK_END)
        self.buffer.write(content.encode(encoding))

    def writeb(self, content: bytes) -> None:
        self.buffer.seek(0, SEEK_END)
        self.buffer.write(content)

    def copy_into(self, dst: IO[bytes], buffer_size: int = 64 * 1024) -> None:
        """Stream the buffer contents into a destination file-like object.

        This avoids materializing a second full copy of the payload; only a
        small fixed-size chunk is held in memory at a time.
        """
        self.buffer.seek(0)
        shutil.copyfileobj(self.buffer, dst, buffer_size)

    @cached_property
    def mime_type(self) -> str:
        """Get the mime type for the content.

        This will be auto-detected if not set explicitly.
        """
        if self._explicit_mime_type:
            return self._explicit_mime_type
        self.buffer.seek(0)
        header = self.buffer.read(2048)
        mime = magic.from_buffer(header, mime=True)
        self.buffer.seek(0, SEEK_END)
        return mime

    def data_url(self) -> str:
        """Get a data URL for the content."""
        # Resolve the mime type first: it may read from the buffer, which is
        # incompatible with holding an exported memoryview.
        mime_type = self.mime_type
        # Encode directly from a zero-copy view of the buffer to avoid the
        # extra full copy that `content()` (getvalue) would create.
        encoded = base64.b64encode(self.view()).decode()
        return f"data:{mime_type};base64,{encoded}"
