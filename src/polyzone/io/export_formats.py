"""Polygon export helpers."""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

Point = Tuple[float, float]


def export_to_yolo(points: Sequence[Point], width: float, height: float) -> List[float]:
    """Return normalized polygon coordinates compatible with YOLO segmentation."""
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive values")

    normalized: List[float] = []
    for x, y in points:
        normalized.extend([x / width, y / height])
    return normalized


def export_to_coco(points: Iterable[Point]) -> List[float]:
    """Return flattened COCO segmentation array."""
    flattened: List[float] = []
    for x, y in points:
        flattened.extend([float(x), float(y)])
    return flattened
