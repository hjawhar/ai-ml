"""Geometry and text primitives shared by the whole package.

Nothing here imports PaddleOCR: these types are the boundary between the OCR
engine and everything downstream.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence


@dataclass(frozen=True, slots=True)
class BBox:
    """Axis-aligned bounding box in pixel coordinates, origin at top-left."""

    x0: float
    y0: float
    x1: float
    y1: float

    @classmethod
    def from_polygon(cls, polygon: Iterable[Sequence[float]]) -> "BBox":
        """Build the enclosing box of a detection polygon.

        PaddleOCR emits quads in visual order (top-left first), so for rotated
        or skewed text the first point is not the minimum corner. Take extremes
        over every vertex instead of trusting point order. Values are coerced to
        ``float`` because PaddleOCR hands back ``numpy`` scalars, which are not
        JSON-serializable.
        """
        xs: list[float] = []
        ys: list[float] = []
        for point in polygon:
            xs.append(float(point[0]))
            ys.append(float(point[1]))
        if not xs:
            raise ValueError("polygon has no points")
        return cls(min(xs), min(ys), max(xs), max(ys))

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def vertical_overlap_ratio(self, other: "BBox") -> float:
        """Shared vertical extent as a fraction of the shorter box's height.

        Normalising by the shorter box keeps a tall heading and a small value
        printed on the same visual row from being torn apart.
        """
        overlap = min(self.y1, other.y1) - max(self.y0, other.y0)
        if overlap <= 0:
            return 0.0
        shorter = min(self.height, other.height)
        if shorter <= 0:
            return 0.0
        return overlap / shorter

    def to_list(self) -> list[float]:
        return [float(self.x0), float(self.y0), float(self.x1), float(self.y1)]


@dataclass(frozen=True, slots=True)
class TextLine:
    """One text line as detected and recognised by PaddleOCR."""

    text: str
    confidence: float
    bbox: BBox

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "confidence": round(float(self.confidence), 4),
            "bbox": self.bbox.to_list(),
        }
