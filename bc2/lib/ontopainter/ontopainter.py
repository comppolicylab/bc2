from enum import Enum
from typing import Callable

import pymupdf
from pydantic import BaseModel, model_validator

from bc2.core.common.ontology import (
    Cited,
    PoliceReport,
    PoliceReportParseResult,
    SourceChunk,
)


class OntoPainterMark(Enum):
    RECT = "RECT"


FieldAccessor = Callable[[PoliceReport], list[Cited]]


class OntoPainterFieldConfig(BaseModel):
    field: str | None = None  # TODO - validate against PoliceReport fields
    label: str | None = None
    mark: OntoPainterMark
    fill: tuple[float, float, float] | None = None
    stroke: tuple[float, float, float] | None = None
    stroke_width: float = 0
    accessor: FieldAccessor | None = None

    @model_validator(mode="after")
    def validate_field_accessor(self) -> "OntoPainterFieldConfig":
        """Either field or accessor must be set, but not both."""
        if not ((self.field is None) ^ (self.accessor is None)):
            raise ValueError("Either field or accessor must be set, but not both.")
        return self

    def get_value(self, report: PoliceReport) -> list[Cited]:
        """Get value of a field from the report.

        Use the `field` attribute if set, otherwise use the `accessor` function.
        """
        v: Cited | list[Cited | None] | list[Cited] | None = None
        if self.field is None:
            if not self.accessor:
                raise ValueError("Accessor is required if field is not set.")
            v = self.accessor(report)
        else:
            v = getattr(report, self.field)

        # Normalize none into an empty list.
        if v is None:
            return []
        # Normalize singular value to a one-item list.
        elif isinstance(v, Cited):
            return [v]
        # Normalize list of Optional values to a list of Cited values.
        elif isinstance(v, list):
            return [v for v in v if v is not None]
        raise ValueError(f"Unexpected type: {type(v)}")


class OntoPainter(BaseModel):
    fields: list[OntoPainterFieldConfig]

    def paint(
        self,
        pdf: str | pymupdf.Document,
        parse_result: PoliceReportParseResult,
        pages: str | None = None,
    ) -> pymupdf.Document:
        """Paint a document annotated with the parse result."""
        # 1. Load the requested pages from the input path / doc
        doc = self._load_pdf(pdf, pages)

        # 2. Loop over field configs and paint each field.
        for field_config in self.fields:
            field_values = field_config.get_value(parse_result.report)
            for i, field_value in enumerate(field_values):
                for j, chunk_id in enumerate(field_value.ids):
                    chunk = parse_result.chunks[chunk_id]
                    self._paint_field(
                        doc,
                        field_config,
                        chunk,
                        label=f"{field_config.label} {i + 1}-{j + 1}",
                    )

        return doc

    def _paint_field(
        self,
        doc: pymupdf.Document,
        field_config: OntoPainterFieldConfig,
        chunk: SourceChunk,
        label: str | None = None,
    ) -> None:
        """Paint a field on a document."""
        match field_config.mark:
            case OntoPainterMark.RECT:
                self._paint_rect(doc, field_config, chunk)
            case _:
                raise ValueError(f"Unsupported mark: {field_config.mark}")
        if label:
            page = doc.load_page(chunk.regions[0].page)
            page_width, page_height = page.mediabox[2:]
            scaled_points = [
                (p[0] * page_width, p[1] * page_height) for p in chunk.regions[0].points
            ]
            x, y = scaled_points[0]
            # Offset to avoid overlapping with bounding rectangle
            y -= 2
            page.insert_text(
                (x, y), label, fontsize=5, fill=field_config.stroke, color=(1, 1, 1)
            )

    def _paint_rect(
        self,
        doc: pymupdf.Document,
        field_config: OntoPainterFieldConfig,
        chunk: SourceChunk,
    ) -> None:
        """Paint a rectangle on a document."""
        for region in chunk.regions:
            # The coordinates come normalized in (0, 1) space. Project into page coords.
            page = doc.load_page(region.page)
            page_width, page_height = page.mediabox[2:]
            shape = page.new_shape()
            scaled_points = [
                (p[0] * page_width, p[1] * page_height) for p in region.points
            ]
            shape.draw_rect(pymupdf.Quad(*scaled_points).rect)
            shape.finish(color=field_config.stroke, width=field_config.stroke_width)
            shape.commit()

    def _load_pdf(
        self, doc: str | pymupdf.Document, pages: str | None = None
    ) -> pymupdf.Document:
        """Load a PDF document."""
        if isinstance(doc, str):
            with open(doc, "rb") as f:
                pdf_doc = pymupdf.open(f)
        else:
            pdf_doc = doc

        filter_pages = _parse_pages_range(pages)
        if filter_pages:
            pdf_doc.select(filter_pages)

        return pdf_doc


def _parse_pages_range(pages: str | None = None) -> list[int] | None:
    """Parse page range specification as a list of page numbers.

    If no spec is given, return None.

    Spec looks like:
      1      Single page
      1-3    Range of pages
      1,2,3  List of pages
      1-3,5  Range and list of pages

    Args:
        pages: The page range specification, 1-indexed.

    Returns:
        A list of page numbers (0-indexed).
    """
    if pages is None:
        return None
    page_list = list[int]()
    for segment in pages.split(","):
        if "-" in segment:
            start, end = segment.split("-")
            page_list.extend(range(int(start.strip()), int(end.strip()) + 1))
        else:
            page_list.append(int(segment.strip()))
    # Clean up duplicates and sort.
    return sorted([x - 1 for x in set(page_list)])
