from typing import Union

from .noop import NoOpRedactConfig
from .openai import OpenAIRedactConfig

RedactConfig = Union[OpenAIRedactConfig, NoOpRedactConfig]
