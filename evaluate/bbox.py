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

    def __init__(self, p0: Point, p1: Point, p2: Point, p3: Point):
        self._points = (p0, p1, p2, p3)

    def scale(self, w: float, h: float) -> "BoundingBox":
        """Scale the bounding box by the given width and height."""
        new_pts = [Point(p.x * w, p.y * h) for p in self._points]
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
