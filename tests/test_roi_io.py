import json
from datetime import datetime

import pytest

from polyzone.io import load_roi, save_roi


def test_save_roi_appends_entries(tmp_path):
    config_path = tmp_path / "config" / "roi.json"
    entry = save_roi(
        video_stem="camera1",
        roi_entry={
            "name": "door",
            "points": [(0, 0), (10, 0), (10, 10)],
            "color": (255, 0, 0),
        },
        output=str(config_path),
        export_format="json",
    )

    datetime.fromisoformat(entry["created_at"])
    data = json.loads(config_path.read_text())
    zones = data["videos"]["camera1"]["zones"]
    assert zones[0]["name"] == "door"
    assert zones[0]["points"] == [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0]]


def test_save_roi_yolo_requires_image_size(tmp_path):
    config_path = tmp_path / "roi.json"
    with pytest.raises(ValueError):
        save_roi(
            video_stem="clip",
            roi_entry={"name": "yolo", "points": [(1, 1), (2, 2), (3, 3)]},
            output=str(config_path),
            export_format="yolo",
        )


def test_save_roi_with_yolo_export(tmp_path):
    config_path = tmp_path / "roi.json"
    save_roi(
        video_stem="clip",
        roi_entry={"name": "yolo", "points": [(1, 1), (2, 2), (3, 3)]},
        output=str(config_path),
        export_format="yolo",
        image_size=(10, 10),
    )
    payload = json.loads(config_path.read_text())
    yolo_entry = payload["videos"]["clip"]["zones"][0]["export"]
    assert yolo_entry["format"] == "yolo"
    assert yolo_entry["image_size"] == {"width": 10, "height": 10}
    assert pytest.approx(yolo_entry["data"][0], rel=1e-7) == 0.1


def test_load_roi_handles_missing_and_invalid(tmp_path):
    missing = load_roi("missing", roi_file=str(tmp_path / "absent.json"))
    assert missing == []

    invalid_path = tmp_path / "broken.json"
    invalid_path.write_text("{not-json}")
    assert load_roi("anything", roi_file=str(invalid_path)) == []


def test_load_roi_returns_zones(tmp_path):
    config_path = tmp_path / "roi.json"
    save_roi(
        video_stem="video1",
        roi_entry={"name": "zone", "points": [(1, 1), (1, 2), (2, 1)]},
        output=str(config_path),
    )
    zones = load_roi("video1", roi_file=str(config_path))
    assert zones[0]["name"] == "zone"
