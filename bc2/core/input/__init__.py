from typing import Union

from .azureblob import AzureBlobInputConfig
from .file import FileInputConfig
from .memory import MemoryInputConfig
from .stdin import StdinInputConfig

InputConfig = Union[
    AzureBlobInputConfig, FileInputConfig, StdinInputConfig, MemoryInputConfig
]
