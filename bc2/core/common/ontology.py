from typing import Generic, TypedDict, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")

# Maximum number of chunk IDs that can be cited for a single field value.
# OpenAI's structured outputs do not support `uniqueItems`, so we cap the
# list length instead. The cap should be high enough that legitimate
# citations are never truncated, but low enough that a model stuck in a
# degenerate-generation loop (repeating the same ID over and over) hits the
# limit before exhausting the context window.
MAX_CITED_IDS = 2048


class Cited(BaseModel, Generic[T]):
    # IDs point to the index of a chunk returned in the
    # PoliceReportParseResult.chunks list. Ideally this would be a `set` to
    # inhibit "degenerate generation" (where a model gets stuck in a loop
    # repeating the same ID until it hits another failure state like max
    # tokens), but OpenAI structured outputs reject `uniqueItems`. Instead
    # we use a bounded list, lean on the field description to instruct the
    # model, and dedupe in a validator below.
    ids: list[int] = Field(
        max_length=MAX_CITED_IDS,
        description=(
            "Indices of the source chunks that support this value. Each index "
            "must appear at most once; do not repeat the same ID. Include "
            "only the chunks that are actually relevant -- typically just one "
            "or two."
        ),
    )
    content: T

    @field_validator("ids", mode="after")
    @classmethod
    def _dedupe_ids(cls, ids: list[int]) -> list[int]:
        return sorted(set(ids))


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
