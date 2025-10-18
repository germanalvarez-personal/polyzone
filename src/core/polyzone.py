"""Shapely-powered SDK for evaluating polygon zones."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from shapely.geometry import Point, Polygon, box

from polyzone.io import load_roi

BBox = Tuple[float, float, float, float]


@dataclass(frozen=True)
class ZoneGeometry:
    """In-memory representation of a stored ROI."""

    name: str
    polygon: Polygon
    color: Sequence[int] | None = None


class Polyzone:
    """Lightweight access layer for polygon containment queries."""

    def __init__(self, video_key: str, roi_file: str = "config/roi.json") -> None:
        self.video_key = video_key
        self.roi_file = roi_file
        self._zones: List[ZoneGeometry] = self._load_zones()

    def zone_names(self) -> List[str]:
        """Return all known zone names for the loaded video key."""
        return [zone.name for zone in self._zones]

    def contains_point(self, x: float, y: float, zone_name: str | None = None) -> bool:
        """Return True if the point lies within (or on the edge of) any zone."""
        target_zones = self._select_zones(zone_name)
        if not target_zones:
            return False

        probe = Point(float(x), float(y))
        return any(zone.polygon.contains(probe) or zone.polygon.touches(probe) for zone in target_zones)

    def intersects_bbox(self, bbox: BBox, zone_name: str | None = None) -> bool:
        """Return True if the bounding box intersects any zone."""
        if len(bbox) != 4:
            raise ValueError("bbox must be a tuple of four coordinates: (x1, y1, x2, y2)")

        x1, y1, x2, y2 = (float(coord) for coord in bbox)
        min_x, max_x = sorted((x1, x2))
        min_y, max_y = sorted((y1, y2))
        region = box(min_x, min_y, max_x, max_y)

        target_zones = self._select_zones(zone_name)
        if not target_zones:
            return False

        return any(zone.polygon.intersects(region) for zone in target_zones)

    def _load_zones(self) -> List[ZoneGeometry]:
        raw_zones = load_roi(self.video_key, roi_file=self.roi_file)
        zones: List[ZoneGeometry] = []
        for zone in raw_zones:
            polygon = Polygon(zone.get("points", []))
            if polygon.is_empty or not polygon.is_valid:
                continue
            zones.append(
                ZoneGeometry(
                    name=zone.get("name", f"zone-{len(zones) + 1}"),
                    polygon=polygon,
                    color=zone.get("color"),
                )
            )
        return zones

    def _select_zones(self, zone_name: str | None) -> Iterable[ZoneGeometry]:
        if zone_name is None:
            return self._zones
        return [zone for zone in self._zones if zone.name == zone_name]
