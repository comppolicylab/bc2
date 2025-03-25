from typing import Union

from .annotations import AnnotationsInspectConfig
from .masked_subjects import OpenAIMaskedSubjectsInspectConfig
from .placeholders import OpenAIPlaceholdersInspectConfig
from .quality import InspectQualityConfig

InspectConfig = Union[
    AnnotationsInspectConfig,
    OpenAIPlaceholdersInspectConfig,
    OpenAIMaskedSubjectsInspectConfig,
    InspectQualityConfig,
]
