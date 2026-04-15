from enum import Enum
from typing import Callable

import pymupdf
from pydantic import BaseModel, model_validator

from ..common.ontology import Cited, PoliceReport, PoliceReportParseResult, SourceChunk
from ..common.palette import Palette


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
        pdf_path: str,
        parse_result: PoliceReportParseResult,
        pages: str | None = None,
    ) -> pymupdf.Document:
        """Paint a document annotated with the parse result."""
        # 1. Load the input path.
        doc = self._load_pdf(pdf_path, pages)

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
            page = doc.load_page(chunk.regions[0].page)
            page_width, page_height = page.mediabox[2:]
            shape = page.new_shape()
            scaled_points = [
                (p[0] * page_width, p[1] * page_height) for p in region.points
            ]
            shape.draw_rect(pymupdf.Quad(*scaled_points).rect)
            shape.finish(color=field_config.stroke, width=field_config.stroke_width)
            shape.commit()

    def _load_pdf(self, pdf_path: str, pages: str | None = None) -> pymupdf.Document:
        """Load a PDF document."""
        with open(pdf_path, "rb") as f:
            doc = pymupdf.open(f)

        filter_pages = _parse_pages_range(pages)
        if filter_pages:
            doc.select(filter_pages)

        return doc


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


default_onto_painter = OntoPainter(
    fields=[
        OntoPainterFieldConfig(
            field="case_number",
            label="Case Number",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Red1,
            stroke_width=2,
        ),
        OntoPainterFieldConfig(
            field="location",
            label="Location",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Green1,
            stroke_width=2,
        ),
        OntoPainterFieldConfig(
            field="incident_type",
            label="Incident Type",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Blue1,
            stroke_width=2,
        ),
        OntoPainterFieldConfig(
            field="reporting_agency",
            label="Reporting Agency",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Purple1,
            stroke_width=2,
        ),
        OntoPainterFieldConfig(
            field="narratives",
            label="Narrative",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Blue1,
            stroke_width=2,
        ),
        # Subject fields:
        # type, name, address, phone, race, sex, dob
        OntoPainterFieldConfig(
            accessor=lambda report: [subject.type for subject in report.subjects],
            label="Subject Type",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Cyan1,
            stroke_width=2,
        ),
        OntoPainterFieldConfig(
            accessor=lambda report: [subject.name for subject in report.subjects],
            label="Subject",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Cyan1,
            stroke_width=2,
        ),
        OntoPainterFieldConfig(
            accessor=lambda report: [subject.address for subject in report.subjects],
            label="Subject Address",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Cyan1,
            stroke_width=2,
        ),
        OntoPainterFieldConfig(
            accessor=lambda report: [subject.phone for subject in report.subjects],
            label="Subject Phone",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Cyan1,
            stroke_width=2,
        ),
        OntoPainterFieldConfig(
            accessor=lambda report: [subject.race for subject in report.subjects],
            label="Subject Race",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Cyan1,
            stroke_width=2,
        ),
        OntoPainterFieldConfig(
            accessor=lambda report: [subject.sex for subject in report.subjects],
            label="Subject Sex",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Cyan1,
            stroke_width=2,
        ),
        OntoPainterFieldConfig(
            accessor=lambda report: [subject.dob for subject in report.subjects],
            label="Subject DOB",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Cyan1,
            stroke_width=2,
        ),
        OntoPainterFieldConfig(
            accessor=lambda report: [subject.dob for subject in report.subjects],
            label="Subject DOB",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Cyan1,
            stroke_width=2,
        ),
        # Offense fields:
        # crime, code
        OntoPainterFieldConfig(
            accessor=lambda report: [offense.crime for offense in report.offenses],
            label="Offense Crime",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Orange1,
            stroke_width=2,
        ),
        OntoPainterFieldConfig(
            accessor=lambda report: [offense.code for offense in report.offenses],
            label="Offense Code",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Orange1,
            stroke_width=2,
        ),
        OntoPainterFieldConfig(
            accessor=lambda report: [offense.statute for offense in report.offenses],
            label="Offense Statute",
            mark=OntoPainterMark.RECT,
            fill=None,
            stroke=Palette.Orange1,
            stroke_width=2,
        ),
    ]
)
