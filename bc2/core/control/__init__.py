from typing import Union

from .chunk import ChunkConfig
from .compose import ComposeConfig

ControlConfig = Union[ChunkConfig, ComposeConfig]
