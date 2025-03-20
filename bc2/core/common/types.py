try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from abc import ABC, abstractmethod
from xml.sax.saxutils import escape as xml_escape

_NameMap = dict[str, str]
"""A mapping of human names to aliases.

This could be name to alias, or ID to name, etc.

Example:
{
    "Leopold Nudell": "Accused 1",
}

As this is really just a generic dictionary, it's confusing to wield it correctly.
DO NOT use this as a top-level type. Instead, see subclasses of `_NameMapContainer`
to find the correct mapping.
"""

_VerboseNameMap = list[dict[str, str]]


class _NameMapContainer(ABC):
    """Wrapper for `_NameMap`.

    Do not use this directly; see subclasses.
    """

    @classmethod
    def merge(cls, *maps: "_NameMapContainer | None") -> Self | None:
        """Merge multiple maps together."""
        real_maps = [m for m in maps if m]

        # If there are no input maps, return None
        if not real_maps:
            return None

        # Merge all the actual maps.
        merged = cls()
        for m in real_maps:
            merged._map.update(m._map)

        return merged

    @property
    @abstractmethod
    def collection_label(self) -> str: ...

    @property
    @abstractmethod
    def item_label(self) -> str: ...

    @property
    @abstractmethod
    def key_label(self) -> str: ...

    @property
    @abstractmethod
    def value_label(self) -> str: ...

    def __init__(self) -> None:
        self._map: _NameMap = {}

    def _set_value(self, key: str, value: str):
        self._map[key] = value

    def to_xml(self) -> str:
        """Convert the map to XML."""
        xml = f"<{self.collection_label}>"
        for key, value in self._map.items():
            xml += f"<{self.item_label}>"
            xml += f"<{self.key_label}>{xml_escape(key)}</{self.key_label}>"
            xml += f"<{self.value_label}>{xml_escape(value)}</{self.value_label}>"
            xml += f"</{self.item_label}>"
        xml += f"</{self.collection_label}>"
        return xml

    def to_json(self) -> _VerboseNameMap:
        """Convert the map to a dictionary."""
        return [
            {self.key_label: key, self.value_label: value}
            for key, value in self._map.items()
        ]


class NameToReplacementMap(_NameMapContainer):
    """A mapping of names to replacement values.

    example:
        rm = NameToReplacementMap()
        rm.set_replacement_text("Leopold Nudell", "Accused 1")
    """

    @property
    def collection_label(self) -> str:
        return "Names"

    @property
    def item_label(self) -> str:
        return "Name"

    @property
    def key_label(self) -> str:
        return "RealName"

    @property
    def value_label(self) -> str:
        return "ReplacementText"

    def set_replacement_text(
        self, name: str, replacement: str
    ) -> "NameToReplacementMap":
        self._set_value(name, replacement)
        return self


class IdToNameMap(_NameMapContainer):
    """A mapping of IDs to human names.

    example:
        im = IdToNameMap()
        im.set_name("1234", "Leopold Nudell")
    """

    @property
    def collection_label(self) -> str:
        return "Names"

    @property
    def item_label(self) -> str:
        return "Name"

    @property
    def key_label(self) -> str:
        return "ID"

    @property
    def value_label(self) -> str:
        return "RealName"

    def set_name(self, id: str, name: str) -> "IdToNameMap":
        self._set_value(id, name)
        return self
