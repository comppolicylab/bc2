import os

from .example import ExampleDoc
from .io import LocalFileReader


def evaluate():
    fr = LocalFileReader(os.path.expanduser("~/Downloads/"))
    return ExampleDoc.load(fr, "14-10133-Redacted.pdf")
