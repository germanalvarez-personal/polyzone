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

    if isinstance(zones, list):
        return zones
    return []
