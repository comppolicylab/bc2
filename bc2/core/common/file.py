import base64
from functools import cached_property
from io import SEEK_END, BytesIO

import magic


class MemoryFile:
    def __init__(self, content: bytes = b"", mime_type: str | None = None):
        self.buffer = BytesIO(content)
        self._explicit_mime_type = mime_type

    def content(self):
        return self.buffer.getvalue()

    def write(self, content: str, encoding: str = "utf-8") -> None:
        self.buffer.seek(0, SEEK_END)
        self.buffer.write(content.encode(encoding))

    def writeb(self, content: bytes) -> None:
        self.buffer.seek(0, SEEK_END)
        self.buffer.write(content)

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
        return (
            f"data:{self.mime_type};base64,{base64.b64encode(self.content()).decode()}"
        )
