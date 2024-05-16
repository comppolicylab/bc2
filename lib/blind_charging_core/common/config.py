from typing import Literal, Union

from pydantic import BaseModel, Field

from ..extract.azuredi import AzureDIExtractConfig
from ..extract.openai import OpenAIExtractConfig
from ..redact.openai import OpenAIRedactConfig


class AzureBlobConfig(BaseModel):
    """Azure Blob config."""

    engine: Literal["azureblob"]
    connection_string: str
    container: str
    prefix: str = Field("")


class AzureBlobInputConfig(BaseModel):
    """Azure Blob input config."""

    engine: Literal["azureblob"]
    name: str
    blob: AzureBlobConfig


class LocalInputConfig(BaseModel):
    """Local input config."""

    engine: Literal["local"]
    path: str


InputConfig = Union[AzureBlobInputConfig, LocalInputConfig]


ExtractConfig = Union[AzureDIExtractConfig, OpenAIExtractConfig]


RedactConfig = Union[OpenAIRedactConfig]


class PdfRenderConfig(BaseModel):
    """PDF Render config."""

    engine: Literal["pdf"]


class HtmlRenderConfig(BaseModel):
    """HTML Render config."""

    engine: Literal["html"]


class TextRenderConfig(BaseModel):
    """Text Render config."""

    engine: Literal["text"]


RenderConfig = Union[PdfRenderConfig, HtmlRenderConfig, TextRenderConfig]


class LocalOutputConfig(BaseModel):
    """File output config."""

    engine: Literal["local"]
    path: str


class AzureBlobOutputConfig(BaseModel):
    """Azure Blob output config."""

    engine: Literal["azureblob"]
    name: str
    blob: AzureBlobConfig


OutputConfig = Union[LocalOutputConfig, AzureBlobOutputConfig]


class PipelineConfig(BaseModel):
    """Pipeline config."""

    input: InputConfig
    extract: ExtractConfig
    redact: RedactConfig
    render: RenderConfig
    output: OutputConfig
