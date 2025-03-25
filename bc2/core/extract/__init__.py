from typing import Union

from .azuredi import AzureDIExtractConfig
from .openai import OpenAIExtractConfig
from .raw import RawExtractConfig
from .tesseract import TesseractExtractConfig

ExtractConfig = Union[
    AzureDIExtractConfig,
    OpenAIExtractConfig,
    TesseractExtractConfig,
    RawExtractConfig,
]
