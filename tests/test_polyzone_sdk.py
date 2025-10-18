import json
from pathlib import Path

import pytest

from core import Polyzone


def _write_roi(tmp_path: Path, payload: dict) -> Path:
    roi_path = tmp_path / "roi.json"
    roi_path.write_text(json.dumps(payload))
    return roi_path


def _default_payload() -> dict:
    return {
        "videos": {
            "sample": {
                "zones": [
                    {
                        "name": "main",
                        "points": [[0, 0], [10, 0], [10, 10], [0, 10]],
                    },
                    {
                        "name": "corner",
                        "points": [[20, 20], [30, 20], [30, 30], [20, 30]],
                    },
                ]
            }
        }
    }


def test_zone_names_and_point_queries(tmp_path):
    roi_file = _write_roi(tmp_path, _default_payload())
    sdk = Polyzone("sample", roi_file=str(roi_file))

    assert set(sdk.zone_names()) == {"main", "corner"}
    assert sdk.contains_point(5, 5)
    assert sdk.contains_point(5, 5, zone_name="main")
    assert not sdk.contains_point(15, 15, zone_name="main")
    assert not sdk.contains_point(5, 5, zone_name="corner")


def test_intersects_bbox(tmp_path):
    roi_file = _write_roi(tmp_path, _default_payload())
    sdk = Polyzone("sample", roi_file=str(roi_file))

    assert sdk.intersects_bbox((2, 2, 4, 4))
    assert sdk.intersects_bbox((2, 2, 4, 4), zone_name="main")
    assert not sdk.intersects_bbox((2, 2, 4, 4), zone_name="corner")
    assert not sdk.intersects_bbox((100, 100, 110, 110))


def test_intersects_bbox_validates_input(tmp_path):
    roi_file = _write_roi(tmp_path, _default_payload())
    sdk = Polyzone("sample", roi_file=str(roi_file))

    with pytest.raises(ValueError):
        sdk.intersects_bbox((1, 2, 3), zone_name=None)


def test_missing_zones(tmp_path):
    roi_file = _write_roi(tmp_path, {"videos": {}})
    sdk = Polyzone("unknown", roi_file=str(roi_file))
    assert sdk.zone_names() == []
    assert not sdk.contains_point(0, 0)
    assert not sdk.intersects_bbox((0, 0, 1, 1))
