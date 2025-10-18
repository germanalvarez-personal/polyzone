from __future__ import annotations

from typing import List

import numpy as np
import pytest

from ui.roi_creator import ROICreator, ZoneDefinition


class StubCV2:
    EVENT_LBUTTONDOWN = 1
    EVENT_RBUTTONDOWN = 2
    WINDOW_NORMAL = 0
    FONT_HERSHEY_SIMPLEX = 0
    LINE_AA = 0

    def __init__(self):
        self.wait_keys: List[int] = [27]  # Exit immediately

    def namedWindow(self, *args, **kwargs):
        return None

    def setMouseCallback(self, *args, **kwargs):
        return None

    def imshow(self, *args, **kwargs):
        return None

    def waitKey(self, _delay: int) -> int:
        return self.wait_keys.pop(0) if self.wait_keys else 27

    def destroyWindow(self, *args, **kwargs):
        return None

    def rectangle(self, *args, **kwargs):
        return None

    def putText(self, *args, **kwargs):
        return None

    def circle(self, *args, **kwargs):
        return None

    def line(self, *args, **kwargs):
        return None


def test_roi_creator_zone_flow(monkeypatch, tmp_path):
    stub_cv2 = StubCV2()
    monkeypatch.setattr("ui.roi_creator.cv2", stub_cv2)
    monkeypatch.setattr(
        ROICreator,
        "_load_source",
        lambda self, path: np.zeros((10, 10, 3), dtype=np.uint8),
    )

    frame_path = tmp_path / "frame.png"
    frame_path.write_text("")

    updates: List[int] = []

    creator = ROICreator(frame_path, on_update=lambda zones: updates.append(len(zones)))

    creator._handle_click(stub_cv2.EVENT_LBUTTONDOWN, 1, 2, None, None)
    creator._handle_click(stub_cv2.EVENT_LBUTTONDOWN, 3, 4, None, None)
    creator._handle_click(stub_cv2.EVENT_LBUTTONDOWN, 5, 6, None, None)
    creator._handle_click(stub_cv2.EVENT_RBUTTONDOWN, 0, 0, None, None)
    creator._handle_click(stub_cv2.EVENT_LBUTTONDOWN, 5, 6, None, None)

    creator._request_zone_finalization(exit_after=False)
    creator._compose_frame()
    assert creator._naming_active
    creator._typed_name = list("custom-zone")
    creator._name_dirty = True
    creator._commit_pending_zone()

    assert creator.zones[0].name == "custom-zone"
    assert creator.zones[0].points[-1] == (5, 6)
    assert updates

    zones = creator.start()
    assert zones == creator.zones


def _build_creator(monkeypatch, tmp_path):
    stub_cv2 = StubCV2()
    monkeypatch.setattr("ui.roi_creator.cv2", stub_cv2)
    monkeypatch.setattr(
        ROICreator,
        "_load_source",
        lambda self, path: np.zeros((10, 10, 3), dtype=np.uint8),
    )
    frame_path = tmp_path / "frame.png"
    frame_path.write_text("")
    creator = ROICreator(frame_path)
    return creator, stub_cv2


def test_roi_creator_naming_cancel(monkeypatch, tmp_path):
    creator, _ = _build_creator(monkeypatch, tmp_path)
    creator._current_points.extend([(0, 0), (1, 1), (2, 2)])
    creator._request_zone_finalization(exit_after=False)

    creator._handle_naming_key(ord("A"))
    creator._handle_naming_key(27)  # ESC cancels

    assert not creator._naming_active
    assert creator._current_points  # polygon still active


def test_roi_creator_commit_exit_after_save(monkeypatch, tmp_path):
    creator, _ = _build_creator(monkeypatch, tmp_path)
    creator._current_points.extend([(0, 0), (5, 0), (5, 5)])
    creator._running = True
    creator._request_zone_finalization(exit_after=True)

    creator._typed_name = []  # trigger default naming
    creator._commit_pending_zone()

    assert creator.zones[0].name == "zone-1"
    assert not creator._running


def test_zone_definition_payload_serialization():
    zone = ZoneDefinition(name="demo", points=[(1, 2), (3, 4), (5, 6)], color=(10, 20, 30))
    payload = zone.as_payload()
    assert payload["name"] == "demo"
    assert payload["points"][0][0] == 1.0
    assert payload["color"] == (10, 20, 30)


def test_zones_payload_export(monkeypatch, tmp_path):
    creator, _ = _build_creator(monkeypatch, tmp_path)
    creator.zones.append(ZoneDefinition(name="demo", points=[(0, 0), (1, 1), (2, 0)], color=(255, 0, 0)))
    payload = creator.zones_payload
    assert payload[0]["name"] == "demo"
    assert pytest.approx(payload[0]["points"][1][0]) == 1.0
