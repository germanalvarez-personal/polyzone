"""Persist ROI data."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Tuple

import copy

from polyzone import get_version

from .export_formats import export_to_coco, export_to_yolo

Point = Tuple[float, float]


def _serialize_points(points: Iterable[Point]) -> list[list[float]]:
    """Convert user supplied points into a serializable list of coordinate pairs."""
    serialized: list[list[float]] = []
    for x, y in points:
        serialized.append([float(x), float(y)])
    return serialized


def _load_payload(path: Path, default: dict) -> dict:
    if not path.exists():
        return copy.deepcopy(default)

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return copy.deepcopy(default)

    if not isinstance(data, dict):
        return copy.deepcopy(default)
    return data


def save_roi(
    video_stem: str,
    roi_entry: dict,
    output: str = "config/roi.json",
    export_format: str = "json",
    image_size: tuple[float, float] | None = None,
) -> dict:
    """Append a new ROI entry under the requested video stem."""
    export_format = export_format.lower()
    if export_format not in {"json", "yolo", "coco"}:
        raise ValueError("export_format must be one of: json, yolo, coco")

    output_path = Path(output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    base_payload = {"polyzone_version": get_version(), "videos": {}}
    payload = _load_payload(output_path, base_payload)

    videos = payload.setdefault("videos", {})
    video_bucket = videos.setdefault(video_stem, {"zones": []})

    if not isinstance(video_bucket.get("zones"), list):
        video_bucket["zones"] = []

    points_data = _serialize_points(roi_entry.get("points", []))
    color_value = roi_entry.get("color")
    if isinstance(color_value, (tuple, list)):
        color_payload = [int(component) for component in color_value]
    else:
        color_payload = color_value
    entry = {
        "name": roi_entry.get("name", f"zone-{len(video_bucket['zones']) + 1}"),
        "points": points_data,
        "color": color_payload,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if export_format == "yolo":
        if not image_size:
            raise ValueError("image_size is required when export_format is 'yolo'")
        width, height = image_size
        entry["export"] = {
            "format": "yolo",
            "data": export_to_yolo(points_data, width=width, height=height),
            "image_size": {"width": width, "height": height},
        }
    elif export_format == "coco":
        entry["export"] = {
            "format": "coco",
            "data": export_to_coco(points_data),
        }

    video_bucket["zones"].append(entry)
    output_path.write_text(json.dumps(payload, indent=2))
    return entry
