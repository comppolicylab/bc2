from typing import Union

from ..control import ControlConfig
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
    ControlConfig,
]
