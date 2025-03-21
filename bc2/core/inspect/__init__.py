from typing import Union

from .annotations import InspectAnnotationsConfig
from .quality import InspectQualityConfig
from .replacements import OpenAIReplacementsInspectConfig
from .subjects import OpenAISubjectsInspectConfig

InspectConfig = Union[
    InspectAnnotationsConfig,
    OpenAIReplacementsInspectConfig,
    OpenAISubjectsInspectConfig,
    InspectQualityConfig,
]
