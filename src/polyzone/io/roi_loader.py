"""ROI loading utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List


def load_roi(video_stem: str, roi_file: str = "config/roi.json") -> List[dict]:
    """Return the stored zones for the requested video stem."""
    path = Path(roi_file).expanduser()
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return []

    videos = data.get("videos", {})
    video_entry = videos.get(video_stem, {})
    zones = video_entry.get("zones", [])

    if not isinstance(zones, list):
        return []

    sanitized: List[dict] = []
    for raw_zone in zones:
        if not isinstance(raw_zone, dict):
            continue
        points = raw_zone.get("points", [])
        normalized_points = []
        for point in points:
            if (
                isinstance(point, (list, tuple))
                and len(point) == 2
                and all(isinstance(coord, (int, float)) for coord in point)
            ):
                normalized_points.append((float(point[0]), float(point[1])))
        if len(normalized_points) < 3:
            continue
        sanitized.append(
            {
                "name": raw_zone.get("name", f"zone-{len(sanitized) + 1}"),
                "points": normalized_points,
                "color": raw_zone.get("color"),
                "export": raw_zone.get("export"),
            }
        )
    return sanitized
