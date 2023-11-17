import json

from azure.ai.formrecognizer._generated.v2022_08_31.models import (
    AnalyzeResultOperation,
    DocumentPage,
)

from .bbox import BoundingBox
from .io import FileIO
from .labeled import LabeledDoc


def load_labeled_doc(reader: FileIO, name: str) -> LabeledDoc:
    """Load a labeled document from a JSON file."""
    path = f"{name}.labels.json"
    d = reader.read(path)
    return LabeledDoc.from_json(d)


def load_ocr_doc(reader: FileIO, name: str) -> AnalyzeResultOperation:
    """Load an OCR document from a JSON file."""
    path = f"{name}.ocr.json"
    s = reader.read(path)
    d = json.loads(s)
    return AnalyzeResultOperation.deserialize(d)


class ExampleDoc:
    """One sample labeled/OCR'd document."""

    @classmethod
    def load(cls, reader: FileIO, name: str):
        labeled = load_labeled_doc(reader, name)
        ocr = load_ocr_doc(reader, name)
        return cls(name, labeled, ocr)

    def __init__(self, name: str, labeled: LabeledDoc, ocr: AnalyzeResultOperation):
        self._name = name
        self._labeled = labeled
        self._ocr = ocr

    @property
    def name(self) -> str:
        return self._name

    @property
    def labeled(self) -> LabeledDoc:
        return self._labeled

    @property
    def ocr(self) -> AnalyzeResultOperation:
        return self._ocr

    @property
    def labels(self) -> dict[str, list[str]]:
        """Infer labels from label boxes and OCR'd text.

        Extracts OCR'd text from the labeled bounding boxes.

        Returns:
            A dictionary of label names to their values.
        """
        labels = {}

        for label in self._labeled.labels:
            texts = list[str]()
            for value in label.value:
                for box in value.boundingBoxes:
                    bbox = BoundingBox.from_flat_list(box)
                    extract = self.text_region(value.page, bbox)
                    texts.append(extract)
            labels[str(label.label)] = texts

        return labels

    def text_region(self, page: int, box: BoundingBox) -> str:
        """Extract text from a region of the OCR'd document.

        Args:
            page: The page number to extract text from.
            box: The bounding box of the region to extract.

        Returns:
            The text in the region.
        """
        ocr_page = self._ocr_page(page)
        scaled = box.scale(ocr_page.width, ocr_page.height)
        words = list[str]()
        spans = dict[int, int]()

        # Find the words that are in the selected region
        for word in ocr_page.words:
            geom = BoundingBox.from_flat_list(word.polygon)
            if scaled | geom:
                words.append(word.content)
                spans[word.span.offset] = len(words) - 1

        paras = list[int]()
        # Find where paragraph breaks are and insert '\n' characters
        for para in self._ocr.analyze_result.paragraphs:
            # Ignore paragraphs on different pages
            if para.bounding_regions[0].page_number != page:
                continue
            offset = para.spans[0].offset
            # Ignore paragraphs that don't have a word in the selected region
            if offset not in spans:
                continue
            word_idx = spans[offset]
            paras.append(word_idx)

        # Build the string with paragraph breaks / spaces
        s = ""
        for i, word in enumerate(words):
            space = ""
            if paras and paras[0] == i:
                paras.pop(0)
                space = "\n"
            else:
                space = " "
            if i > 0:
                s += space
            s += word

        return s

    def _ocr_page(self, page: int) -> DocumentPage:
        """Get the OCR'd page by its number."""
        for p in self._ocr.analyze_result.pages:
            if p.page_number == page:
                return p
        raise ValueError(f"Page {page} not found in OCR'd document")
