from typing import Literal, Union

from pydantic import BaseModel, conlist

# NOTE: The DocumentIntelligence *.labels.json files advertise a JSON schema
# at the following URL:
# https://schema.cognitiveservices.azure.com/formrecognizer/2021-03-01/labels.json
#
# Unfortunately, as of 2024-04-29 that schema no longer exists. Previously, we
# parsed the files according to that JSON schema, but now we just do our own
# parsing. This means we won't catch breaking schema changes, so be careful!


BoundingBox = conlist(float, min_length=8, max_length=8)


class LabelRegionValue(BaseModel):
    page: int
    text: str
    boundingBoxes: list[list[float]] = BoundingBox


class LabelRegion(BaseModel):
    label: str
    value: list[LabelRegionValue]
    labelType: Literal["region"]


Label = Union[LabelRegion]


class LabeledDoc(BaseModel):
    document: str
    labels: list[Label]
