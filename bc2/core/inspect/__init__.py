from typing import Union

from .aliases import OpenAIAliasesInspectConfig
from .annotations import InspectAnnotationsConfig
from .quality import InspectQualityConfig

InspectConfig = Union[
    InspectAnnotationsConfig, OpenAIAliasesInspectConfig, InspectQualityConfig
]
