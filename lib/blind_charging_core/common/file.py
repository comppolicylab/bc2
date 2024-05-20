from io import BytesIO


class MemoryFile:
    def __init__(self, content: bytes = b""):
        self.buffer = BytesIO(content)

    def content(self):
        return self.buffer.getvalue()

    def write(self, content: str, encoding: str = "utf-8") -> None:
        self.buffer.write(content.encode(encoding))

    def writeb(self, content: bytes) -> None:
        self.buffer.write(content)
