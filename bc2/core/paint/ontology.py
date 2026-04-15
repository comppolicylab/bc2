from functools import cached_property
from typing import Literal

import pymupdf
from pydantic import BaseModel

from ..common.file import MemoryFile
from ..common.ontology import PoliceReportParseResult
from ..common.ontopainter import OntoPainter, OntoPainterFieldConfig, OntoPainterMark
from ..common.palette import Palette
from ..common.preprocess import register_preprocessor
from .base import BasePainterDriver

painter = OntoPainter(
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


class OntologyPainterConfig(BaseModel):
    engine: Literal["paint:ontology"] = "paint:ontology"

    @cached_property
    def driver(self) -> "OntologyPainterDriver":
        return OntologyPainterDriver(self)


class OntologyPainterDriver(BasePainterDriver[PoliceReportParseResult]):
    def __init__(self, config: OntologyPainterConfig):
        self.config = config

    @register_preprocessor(r"application/x-ontology")
    def preprocess_ontology(self, file: MemoryFile) -> PoliceReportParseResult:
        """Deserialize an ontology MemoryFile into a PoliceReportParseResult."""
        file.buffer.seek(0)
        return PoliceReportParseResult.model_validate_json(file.buffer.read())

    def paint(self, original: MemoryFile, data: PoliceReportParseResult) -> MemoryFile:
        """Paint the original PDF with ontology annotations."""
        original.buffer.seek(0)
        if original.mime_type != "application/pdf":
            raise ValueError(f"Expected PDF, got {original.mime_type}")
        doc = pymupdf.open(stream=original.buffer.read(), filetype="pdf")

        painted = painter.paint(doc, data)

        out = MemoryFile(mime_type="application/pdf")
        out.writeb(painted.tobytes())
        return out
