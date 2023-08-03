import tomllib
import os

from pathlib import Path
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Blind Charging config."""

    azure_endpoint: str
    azure_key: str

    openai_api_type: str
    openai_api_base: str
    openai_api_version: str
    openai_api_chat_version: str
    openai_api_key: str
    openai_engine: str


_config_path = os.environ.get('CONFIG_PATH', "config.toml")

config = Config.parse_obj(tomllib.loads(Path(_config_path).read_text()))
