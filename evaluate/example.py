import json

from azure.ai.formrecognizer._generated.v2022_08_31.models import AnalyzeResultOperation

from .io import FileReader
from .labeled import LabeledDoc


def load_labeled_doc(reader: FileReader, name: str) -> LabeledDoc:
    """Load a labeled document from a JSON file."""
    path = f"{name}.labels.json"
    d = reader.read(path)
    return LabeledDoc.from_json(d)


def load_ocr_doc(reader: FileReader, name: str) -> AnalyzeResultOperation:
    """Load an OCR document from a JSON file."""
    path = f"{name}.ocr.json"
    s = reader.read(path)
    d = json.loads(s)
    return AnalyzeResultOperation.deserialize(d)


class ExampleDoc:
    """One sample labeled/OCR'd document."""

    @classmethod
    def load(cls, reader: FileReader, name: str):
        labeled = load_labeled_doc(reader, name)
        ocr = load_ocr_doc(reader, name)
        return cls(name, labeled, ocr)

    def __init__(self, name: str, labeled: LabeledDoc, ocr: AnalyzeResultOperation):
        self._name = name
        self._labeled = labeled
        self._ocr = ocr

    @property
    def name(self):
        return self._name

    @property
    def labeled(self):
        return self._labeled

    @property
    def ocr(self):
        return self._ocr
