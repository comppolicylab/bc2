from typing import Union

from .azureblob import AzureBlobOutputConfig
from .file import FileOutputConfig
from .memory import MemoryOutputConfig
from .stdout import StdoutOutputConfig

OutputConfig = Union[
    AzureBlobOutputConfig, FileOutputConfig, StdoutOutputConfig, MemoryOutputConfig
]
