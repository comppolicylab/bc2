from typing import Literal, Union

from pydantic import BaseModel, Field


class AzureBlobConfig(BaseModel):
    """Azure Blob config."""

    engine: Literal["azureblob"]
    connection_string: str
    container: str
    prefix: str = Field("")


class OpenAIApiConfig(BaseModel):
    """OpenAI API settings."""

    type: str
    base: str
    version: str
    chat_version: str
    key: str


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


class AzureDIExtractConfig(BaseModel):
    """Azure DI Extract config."""

    engine: Literal["azuredi"]
    endpoint: str
    key: str
    document_model: str
    min_confidence: float = Field(0.04)
    narrative_field: str = Field("narrative")


class OpenAIExtractConfig(BaseModel):
    """OpenAI Extract config."""

    engine: Literal["openai"]
    api: OpenAIApiConfig
    model: str
    prompt_file: str


ExtractConfig = Union[AzureDIExtractConfig, OpenAIExtractConfig]


class OpenAIRedactConfig(BaseModel):
    """OpenAI Redact config."""

    engine: Literal["openai"]
    api: OpenAIApiConfig
    model: str
    completion_type: Literal["chat", "completion"] = "completion"
    prompt_file: str


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
