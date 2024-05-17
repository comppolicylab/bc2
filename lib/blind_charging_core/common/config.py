from typing import Union

from pydantic import BaseModel

from ..extract.azuredi import AzureDIExtractConfig
from ..extract.openai import OpenAIExtractConfig
from ..input.azureblob import AzureBlobInputConfig
from ..input.file import FileInputConfig
from ..input.stdin import StdinInputConfig
from ..output.azureblob import AzureBlobOutputConfig
from ..output.file import FileOutputConfig
from ..output.stdout import StdoutOutputConfig
from ..redact.openai import OpenAIRedactConfig
from ..render.html import HtmlRenderConfig
from ..render.pdf import PdfRenderConfig
from ..render.text import TextRenderConfig

InputConfig = Union[AzureBlobInputConfig, FileInputConfig, StdinInputConfig]


ExtractConfig = Union[AzureDIExtractConfig, OpenAIExtractConfig]


RedactConfig = Union[OpenAIRedactConfig]


RenderConfig = Union[PdfRenderConfig, HtmlRenderConfig, TextRenderConfig]


OutputConfig = Union[AzureBlobOutputConfig, FileOutputConfig, StdoutOutputConfig]


class PipelineConfig(BaseModel):
    """Pipeline config."""

    input: InputConfig
    extract: ExtractConfig
    redact: RedactConfig
    render: RenderConfig
    output: OutputConfig
