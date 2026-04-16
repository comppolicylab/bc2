from .ontopainter import OntoPainter, OntoPainterFieldConfig, OntoPainterMark
from .palette import Palette

default_painter = OntoPainter(
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
