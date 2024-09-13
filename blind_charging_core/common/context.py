from typing import Any


class Record(dict[str, Any]): ...


class Context(Record, Any):
    """dot.notation access to dictionary attributes."""

    __getattr__ = Record.get  # type: ignore
    __setattr__ = Record.__setitem__  # type: ignore
    __delattr__ = Record.__delitem__  # type: ignore
