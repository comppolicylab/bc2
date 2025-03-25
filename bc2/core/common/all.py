from typing import Union

from ..extract import ExtractConfig
from ..input import InputConfig
from ..inspect import InspectConfig
from ..output import OutputConfig
from ..parse import ParseConfig
from ..redact import RedactConfig
from ..render import RenderConfig

AnyConfig = Union[
    InputConfig,
    ExtractConfig,
    RedactConfig,
    InspectConfig,
    ParseConfig,
    RenderConfig,
    OutputConfig,
    "ChunkConfig",
    "ComposeConfig",
]

# NOTE(jnu): the following two imports support some degree of recursive
# module definition, so there are circular imports. To avoid partial import
# errors, we use a forward-ref above and import the modules at the end of
# this module.
from ..control.chunk import ChunkConfig
from ..control.compose import ComposeConfig
