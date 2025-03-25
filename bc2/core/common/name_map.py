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
    def merge(cls, *maps: "_NameMapContainer | dict[str, str] | None") -> Self:
        """Merge multiple maps together."""
        real_maps = [m for m in maps if m]

        # If there are no input maps, return an empty map
        if not real_maps:
            return cls()

        # Merge all the actual maps.
        merged = cls()
        for m in real_maps:
            if isinstance(m, dict):
                merged._map.update(m)
            else:
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

    def __init__(self, initial_map: _NameMap | None = None) -> None:
        self._map: _NameMap = initial_map.copy() if initial_map else {}

    def _set_value(self, key: str, value: str):
        self._map[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._map

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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._map})"

    def __str__(self) -> str:
        return str(self._map)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, _NameMapContainer):
            return self._map == value._map and self.__class__ == value.__class__
        return super().__eq__(value)


class NameToMaskMap(_NameMapContainer):
    """A mapping of names to placeholder values.

    example:
        rm = NameToMaskMap()
        rm.set_mask("Leopold Nudell", "Accused 1")
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

    def set_mask(self, name: str, mask: str) -> "NameToMaskMap":
        self._set_value(name, mask)
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


class IdToMaskMap(_NameMapContainer):
    """A mapping of IDs to mask values.

    example:
        mm = IdToMaskMap()
        mm.set_mask("1234", "Accused 1")
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
        return "MaskedName"

    def set_mask(self, id: str, mask: str) -> "IdToMaskMap":
        self._set_value(id, mask)
        return self
