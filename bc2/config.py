import os
import tomllib
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class AzureSettings(BaseSettings):
    """Azure settings."""

    endpoint: str
    key: str


class OpenAIApiSettings(BaseSettings):
    """OpenAI API settings."""

    type: str
    base: str
    version: str
    chat_version: str
    key: str


class OpenAISettings(BaseSettings):
    """OpenAI settings."""

    api: OpenAIApiSettings
    engine: str


class ExtractionSettings(BaseSettings):
    """Blind Charging extraction parameters."""

    min_confidence: float = Field(0.04)
    narrative_field: str = Field("narrative")


class BC2Settings(BaseSettings):
    """Blind Charging v2 settings."""

    document_model: str
    cache_dir: str
    output_dir: str
    renderer: str = Field("pdf")
    extraction: ExtractionSettings = Field(ExtractionSettings())


class Config(BaseSettings):
    """Blind Charging config."""

    log_level: str = Field("INFO", env="LOG_LEVEL")

    azure: AzureSettings
    openai: OpenAISettings
    bc2: BC2Settings


_config_path = os.environ.get("CONFIG_PATH", "config.toml")

config = Config.parse_obj(tomllib.loads(Path(_config_path).read_text()))
