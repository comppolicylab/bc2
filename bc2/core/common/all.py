import typing

from ..analyze import AnalyzeConfig
from ..extract import ExtractConfig
from ..input import InputConfig
from ..inspect import InspectConfig
from ..ontology import OntologyConfig
from ..output import OutputConfig
from ..paint import PaintConfig
from ..parse import ParseConfig
from ..redact import RedactConfig
from ..render import RenderConfig

AnyIOConfig = typing.Union[
    InputConfig,
    OutputConfig,
]

AnyProcessingConfig = typing.Union[
    AnalyzeConfig,
    ExtractConfig,
    OntologyConfig,
    PaintConfig,
    RedactConfig,
    InspectConfig,
    ParseConfig,
    RenderConfig,
    "ChunkConfig",
    "ComposeConfig",
]

AnyConfig = typing.Union[
    AnyIOConfig,
    AnyProcessingConfig,
]

# NOTE(jnu): the following two imports support some degree of recursive
# module definition, so there are circular imports. To avoid partial import
# errors, we use a forward-ref above and import the modules at the end of
# this module.
from ..control.chunk import ChunkConfig
from ..control.compose import ComposeConfig
