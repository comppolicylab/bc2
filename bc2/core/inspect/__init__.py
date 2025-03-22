from typing import Union

from .annotations import InspectAnnotationsConfig
from .masked_subjects import OpenAIMaskedSubjectsInspectConfig
from .placeholders import OpenAIPlaceholdersInspectConfig
from .quality import InspectQualityConfig

InspectConfig = Union[
    InspectAnnotationsConfig,
    OpenAIPlaceholdersInspectConfig,
    OpenAIMaskedSubjectsInspectConfig,
    InspectQualityConfig,
]
