from dataclasses import asdict, dataclass
from typing import NamedTuple

Point = NamedTuple("Point", [("x", float), ("y", float)])


class BoundingBox:
    @classmethod
    def from_flat_list(cls, coords: list[float]) -> "BoundingBox":
        """Create a bounding box from a flat list of 8 values."""
        if len(coords) != 8:
            raise ValueError("Expected 8 values")
        return cls(
            Point(coords[0], coords[1]),
            Point(coords[2], coords[3]),
            Point(coords[4], coords[5]),
            Point(coords[6], coords[7]),
        )

    def __init__(self, *args):
        if len(args) == 1:
            self._points = args[0]
        elif len(args) == 4:
            self._points = args
        else:
            raise ValueError("Expected 1 or 4 arguments")

    def scale(self, w: float, h: float) -> "BoundingBox":
        """Scale the bounding box by the given width and height."""
        new_pts = [Point(p.x * w, p.y * h) for p in self._points]
        return BoundingBox(*new_pts)

    def norm(self, w: float, h: float) -> "BoundingBox":
        """Normalize the bounding box by the given width and height."""
        new_pts = [Point(p.x / w, p.y / h) for p in self._points]
        return BoundingBox(*new_pts)

    def overlaps(self, other: "BoundingBox") -> bool:
        """Test if this and other bounding boxes overlap."""
        for p in self._points:
            if other.contains(p):
                return True
        for p in other._points:
            if self.contains(p):
                return True
        return False

    def rect(self) -> list[float]:
        """Return the upper left and lower right corners of the bounding box."""
        min_x = min(p.x for p in self._points)
        min_y = min(p.y for p in self._points)
        max_x = max(p.x for p in self._points)
        max_y = max(p.y for p in self._points)
        return [min_x, min_y, max_x, max_y]

    def contains(self, p: Point) -> bool:
        """Test if this bounding box contains the given point."""
        if p.x < self._points[0].x:
            return False
        if p.x > self._points[2].x:
            return False
        if p.y < self._points[0].y:
            return False
        if p.y > self._points[2].y:
            return False
        return True

    def __or__(self, other: "BoundingBox") -> bool:
        return self.overlaps(other)

    def __repr__(self) -> str:
        return f"BoundingBox({self._points})"


@dataclass
class Label:
    name: str
    value: str | None
    bbox: BoundingBox | None


class Labels:
    def __init__(self):
        self._labels = dict[str, list[Label]]()

    def add(self, name: str, value: str | None, bbox: BoundingBox | None):
        """Add a label to the collection.

        Args:
            name: The name of the label.
            value: The value of the label.
            bbox: The bounding box of the label.
        """
        if name not in self._labels:
            self._labels[name] = []

        if value is None and bbox is not None:
            raise ValueError("Cannot have a bounding box without a value")

        if bbox is None and value is not None:
            raise ValueError("Cannot have a value without a bounding box")

        if bbox is None and value is None:
            return

        self._labels[name].append(Label(name, value, bbox))

    def __repr__(self) -> str:
        return f"Labels({self._labels})"

    def as_dict(self) -> dict[str, list[dict]]:
        """Return the labels as a dictionary."""
        return {k: [asdict(v) for v in vs] for k, vs in self._labels.items()}

    def flat(self) -> list[Label]:
        """Return the labels as a list of rows."""
        return [v for vs in self._labels.values() for v in vs]

    def keys(self) -> set[str]:
        """Return the set of keys in the labels."""
        return set(self._labels.keys())

    def has(self, label: str) -> bool:
        """Return True if the label positively exists."""
        v = self._labels.get(label, None)
        if v:
            return True
        return False

    def equal(self, label: str, other: "Labels") -> bool:
        """Return True if the label has the given value."""
        v0 = self._labels.get(label, None)
        v1 = other._labels.get(label, None)
        if not v0 and not v1:
            return True
        s0 = {v.value for v in v0}
        s1 = {v.value for v in v1}
        return s0 == s1
