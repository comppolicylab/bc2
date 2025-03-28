from typing import Union

from .annotations import AnnotationsInspectConfig
from .embed import EmbedInspectConfig
from .masked_subjects import OpenAIMaskedSubjectsInspectConfig
from .placeholders import OpenAIPlaceholdersInspectConfig
from .quality import InspectQualityConfig

InspectConfig = Union[
    AnnotationsInspectConfig,
    EmbedInspectConfig,
    OpenAIPlaceholdersInspectConfig,
    OpenAIMaskedSubjectsInspectConfig,
    InspectQualityConfig,
]
