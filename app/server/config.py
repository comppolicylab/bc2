import logging
import os
from functools import cached_property
from pathlib import Path
from typing import Literal, Union

import tomllib
from glowplug import MsSqlDriver
from pydantic_settings import BaseSettings


class MsSqlConfig(BaseSettings):
    dialect: Literal["mssql"]
    odbc_driver: Literal["ODBC Driver 17 for SQL Server"] = (
        "ODBC Driver 17 for SQL Server"
    )
    host: str
    port: int
    user: str
    password: str
    database: str

    @cached_property
    def driver(self):
        odbc_driver = self.odbc_driver.replace(" ", "+")
        path = (
            f"{self.user}:{self.password}@{self.host}:{self.port}"
            f"/{self.database}?driver={odbc_driver}"
        )
        return MsSqlDriver(path)


DbConfig = Union[MsSqlConfig]


class Config(BaseSettings):
    debug: bool = False
    db: DbConfig


def _load_config(path: str = os.getenv("CONFIG_PATH", "config.toml")) -> Config:
    """Load the configuration from a TOML file."""
    if not Path(path).exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    raw_cfg = Path(path).read_text()
    cfg = tomllib.loads(raw_cfg)
    return Config.model_validate(cfg)


# The global app configuration
config = _load_config()

# Set up logging
logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO)
