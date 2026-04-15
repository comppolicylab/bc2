from typing import Generic, TypedDict, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Cited(BaseModel, Generic[T]):
    ids: list[int]
    content: T


class Offense(BaseModel):
    crime: Cited[str]
    statute: Cited[str] | None
    code: Cited[str] | None


class Subject(BaseModel):
    seq: Cited[int] | None = None
    type: Cited[str]
    name: Cited[str]
    address: Cited[str]
    phone: Cited[str]
    race: Cited[str]
    sex: Cited[str]
    dob: Cited[str]


class PoliceReport(BaseModel):
    reporting_agency: Cited[str]
    case_number: Cited[str]
    location: Cited[str]
    incident_type: Cited[str]
    subjects: list[Subject]
    narratives: list[Cited[str]]
    offenses: list[Offense]


class SourceChunkSpan(BaseModel):
    offset: int
    length: int


class SourceChunkBoundingRegion(BaseModel):
    page: int
    points: list[tuple[float, float]]  # (x, y) coordinate list


class SourceChunk(BaseModel):
    """Based on AzureDI DocumentParagraph."""

    spans: list[SourceChunkSpan]
    regions: list[SourceChunkBoundingRegion]
    content: str


class PoliceReportParseResult(BaseModel):
    report: PoliceReport
    chunks: list[SourceChunk]


class KeyValuePair(TypedDict):
    key: str
    value: str


Table = list[dict[str, str]]


class Palette:
    Red1 = (0.9, 0.2, 0.1)
    Red2 = (0.8, 0.1, 0.0)
    Red3 = (0.7, 0.0, 0.0)
    Orange1 = (0.9, 0.5, 0.0)
    Orange2 = (0.8, 0.4, 0.0)
    Orange3 = (0.7, 0.3, 0.0)
    Yellow1 = (0.9, 0.9, 0.0)
    Yellow2 = (0.8, 0.8, 0.0)
    Yellow3 = (0.7, 0.7, 0.0)
    Green1 = (0.2, 0.9, 0.1)
    Green2 = (0.1, 0.8, 0.0)
    Green3 = (0.0, 0.7, 0.0)
    Blue1 = (0, 0.5, 1)
    Blue2 = (0.0, 0.4, 0.8)
    Blue3 = (0.0, 0.3, 0.7)
    Purple1 = (0.9, 0.0, 0.9)
    Purple2 = (0.8, 0.0, 0.8)
    Purple3 = (0.7, 0.0, 0.7)
    Pink1 = (0.9, 0.0, 0.9)
    Pink2 = (0.8, 0.0, 0.8)
    Pink3 = (0.7, 0.0, 0.7)
    Brown1 = (0.5, 0.25, 0.0)
    Brown2 = (0.4, 0.2, 0.0)
    Brown3 = (0.3, 0.15, 0.0)
    Cyan1 = (0.0, 0.9, 0.9)
    Cyan2 = (0.0, 0.8, 0.8)
    Cyan3 = (0.0, 0.7, 0.7)
    Lime1 = (0.9, 0.9, 0.0)
    Lime2 = (0.8, 0.8, 0.0)
    Lime3 = (0.7, 0.7, 0.0)
    Maroon1 = (0.5, 0.0, 0.0)
    Maroon2 = (0.4, 0.0, 0.0)
    Maroon3 = (0.3, 0.0, 0.0)
    Gray1 = (0.5, 0.5, 0.5)
    Gray2 = (0.4, 0.4, 0.4)
    Gray3 = (0.3, 0.3, 0.3)
