import os

from .example import ExampleDoc
from .io import LocalFileReader

fr = LocalFileReader(os.path.expanduser("~/Downloads/"))
doc = ExampleDoc.load(fr, "14-10133-Redacted.pdf")
print(doc)
