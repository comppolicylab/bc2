import json
import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class DataTypeInfo(Generic[T]):
    """Information about a data type."""

    name: str
    extension: str
    directory: str
    content_type: T
    load: Callable[[str], T]


DataType = Enum("DataType", "prompt example")
"""Static data types available in the app."""


def _read_text_file(fp: str, encoding: str = "utf-8") -> str:
    """Read a text file.

    Args:
        fp: File path.

    Returns:
        File content.
    """
    with open(fp, "r", encoding=encoding) as f:
        return f.read()


def _read_jsonl_file(fp: str) -> list[T]:
    """Read a JSONL file.

    Args:
        fp: File path.

    Returns:
        List of JSON objects.
    """
    with open(fp, "r") as f:
        return [json.loads(line) for line in f]


# NOTE: Data types are not automatically available through the loader.
# They must be registered here to be used!
_TYPE_REGISTRY: dict[DataType, DataTypeInfo] = {
    DataType.prompt: DataTypeInfo("prompt", "txt", "prompts", str, _read_text_file),
    DataType.example: DataTypeInfo(
        "example", "jsonl", "prompts", list[dict[str, str]], _read_jsonl_file
    ),
}
"""Metadata describing each data type."""


def data_file_path(data_type: DataType, id_: str) -> str:
    """Get the path to a data file given its type and ID."""
    # Data files are stored as ./blind_charging_data/{directory}/{file_id}.{extension}
    # We are in: ./blind_charging_core/common
    metadata = _TYPE_REGISTRY[data_type]
    current_dir = os.path.dirname(__file__)
    sanitized_id = re.sub(r"[^a-zA-Z0-9]", "_", id_)
    fp = os.path.join(
        current_dir,
        "..",
        "..",
        "blind_charging_data",
        metadata.directory,
        f"{sanitized_id}.{metadata.extension}",
    )
    logger.debug(f"Resolved data file path for {metadata.name} {id_}: {fp}")
    return fp


# TODO(jnu): the following functions should be generic over DT,
# and the return type should be DT.content_type. I'm not sure how
# to express this in MyPy right now.
# DT = TypeVar("DT", bound=DataType)


def load_data_file(data_type: DataType, id_: str) -> Any:
    """Load the content of a data file by ID.

    Args:
        data_type: Type of data.
        id_: File ID.

    Returns:
        File content.
    """
    fp = data_file_path(data_type, id_)
    return load_data_file_from_path(data_type, fp)


def load_data_file_from_path(data_type: DataType, fp: str) -> Any:
    """Load the content of a file by its full path.

    Args:
        data_type: Type of data.
        fp: File path.

    Returns:
        File content.
    """
    metadata = _TYPE_REGISTRY[data_type]
    return metadata.load(fp)
