from typing import Generic, TypedDict, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Cited(BaseModel, Generic[T]):
    # IDs are a set pointing to the index of a chunk returned in the
    # PoliceReportParseResult.chunks list. The `set` type is an important
    # constraint that inhibits "degenerate generation," where a model can
    # get stuck in a loop repeating the same ID over and over, ultimately
    # reaching another failure state (like max tokens).
    ids: set[int]
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
