"""Interactive ROI creator supporting images and videos."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Deque, Iterable, List, Sequence, Tuple

import cv2

RGBColor = Tuple[int, int, int]
Point = Tuple[int, int]


def _is_image_path(path: Path) -> bool:
    return path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}


def _centroid(points: Iterable[Point]) -> Point:
    pts = list(points)
    if not pts:
        return (0, 0)
    x_total = sum(x for x, _ in pts)
    y_total = sum(y for _, y in pts)
    return int(x_total / len(pts)), int(y_total / len(pts))


@dataclass(slots=True)
class ZoneDefinition:
    """Captured polygon metadata ready for persistence and rendering."""

    name: str
    points: List[Point]
    color: RGBColor

    def as_payload(self) -> dict:
        return {
            "name": self.name,
            "points": [(float(x), float(y)) for x, y in self.points],
            "color": tuple(int(c) for c in self.color),
        }


class MessageBuffer:
    """Ring buffer for UI messages."""

    def __init__(self, capacity: int = 5) -> None:
        self._messages: Deque[str] = deque(maxlen=capacity)

    def push(self, message: str) -> None:
        self._messages.append(message)

    def entries(self) -> List[str]:
        return list(self._messages)

    def latest_first(self) -> List[str]:
        return list(reversed(self._messages))


class ROICreator:
    """Create polygonal ROIs using OpenCV preview windows."""

    COLOR_PALETTE: Sequence[RGBColor] = [
        (255, 107, 107),
        (78, 205, 196),
        (255, 209, 102),
        (26, 83, 92),
        (255, 159, 28),
    ]

    def __init__(
        self,
        input_path: Path | str,
        window_name: str = "Polyzone ROI Creator",
        on_update: Callable[[List[ZoneDefinition]], None] | None = None,
        export_format: str = "json",
    ) -> None:
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"Input path does not exist: {path}")

        self.path = path
        self.window_name = window_name
        self.on_update = on_update
        self.export_format = export_format
        self.base_image = self._load_source(path)
        self.height, self.width = self.base_image.shape[:2]

        self.zones: List[ZoneDefinition] = []
        self._current_points: List[Point] = []
        self._running = False
        self._messages = MessageBuffer(capacity=6)
        self._messages.push(
            "Left-click: add | Right-click: undo | N: save | S: save+exit | Q/Esc: quit"
        )

        self._naming_active = False
        self._typed_name: List[str] = []
        self._name_dirty = False
        self._pending_zone_points: List[Point] | None = None
        self._exit_after_save = False

    @property
    def zones_payload(self) -> List[dict]:
        """Return zones ready for serialization or persistence."""
        return [zone.as_payload() for zone in self.zones]

    def _load_source(self, path: Path):
        if _is_image_path(path):
            image = cv2.imread(str(path))
            if image is None:
                raise RuntimeError(f"Failed to load image: {path}")
            return image

        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            raise RuntimeError(f"Unable to open video: {path}")

        success, frame = capture.read()
        capture.release()
        if not success or frame is None:
            raise RuntimeError("Failed to read first frame from video.")
        return frame

    def start(self) -> List[ZoneDefinition]:
        """Run the ROI creation loop."""
        self._running = True
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.window_name, self._handle_click)

        try:
            while self._running:
                display_frame = self._compose_frame()
                cv2.imshow(self.window_name, display_frame)
                key = cv2.waitKey(20) & 0xFF

                if key == 255:
                    continue

                if self._naming_active:
                    self._handle_naming_key(key)
                    continue

                if key in {27, ord("q")}:
                    self._log("Session ended by user.")
                    break
                if key in {ord("n"), ord("N")}:
                    self._request_zone_finalization(exit_after=False)
                    continue
                if key in {ord("s"), ord("S")}:
                    if self._current_points:
                        self._request_zone_finalization(exit_after=True)
                    else:
                        self._log("No active polygon. Closing session.")
                        break
                    continue
                if key in {ord("u"), ord("U")}:
                    self._undo_last_point()

            cv2.destroyWindow(self.window_name)
            return self.zones
        finally:
            cv2.setMouseCallback(self.window_name, lambda *args: None)
            self._running = False

    def _handle_click(self, event, x: int, y: int, _flags, _userdata) -> None:
        if self._naming_active:
            return

        if event == cv2.EVENT_LBUTTONDOWN:
            self._current_points.append((x, y))
            self._log(f"Point added at ({x}, {y}).")
            self._notify_update()
        elif event == cv2.EVENT_RBUTTONDOWN and self._current_points:
            removed = self._current_points.pop()
            self._log(f"Point removed at {removed}.")
            self._notify_update()

    def _compose_frame(self):
        frame = self.base_image.copy()

        # Draw stored zones with labels
        for zone in self.zones:
            self._draw_polygon(frame, zone.points, zone.color, close=True)
            self._draw_zone_label(frame, zone)

        # Draw active polygon (closing once we have three points)
        if self._current_points:
            active_color = self._palette_color(len(self.zones))
            should_close = len(self._current_points) >= 3
            self._draw_polygon(frame, self._current_points, active_color, close=should_close, thickness=2)

        self._render_header(frame)
        self._render_messages(frame)
        return frame

    def _render_header(self, frame) -> None:
        header_height = 50 if not self._naming_active else 70
        cv2.rectangle(frame, (0, 0), (self.width, header_height), (0, 0, 0), -1)

        if self._naming_active:
            name_preview = self._current_name() + "_"
            header_text = f"Name zone: {name_preview} | Enter=confirm • Esc=cancel • Backspace=delete"
        else:
            header_text = (
                "Controls: Left-click add • Right-click undo • N save polygon • "
                "S save & exit • U undo • Q/Esc quit"
            )

        cv2.putText(
            frame,
            header_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    def _render_messages(self, frame) -> None:
        messages = self._messages.latest_first()
        if not messages:
            return

        block_height = 20 * len(messages) + 20
        top = self.height - block_height
        cv2.rectangle(frame, (0, top), (self.width, self.height), (0, 0, 0), -1)

        for idx, message in enumerate(messages):
            y = self.height - 10 - idx * 20
            cv2.putText(
                frame,
                message,
                (10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (200, 200, 200),
                1,
                cv2.LINE_AA,
            )

    def _draw_zone_label(self, frame, zone: ZoneDefinition) -> None:
        cx, cy = _centroid(zone.points)
        text = zone.name
        bgr = self._as_bgr(zone.color)
        cv2.putText(
            frame,
            text,
            (max(cx - 40, 5), max(cy - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            3,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            text,
            (max(cx - 40, 5), max(cy - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            bgr,
            1,
            cv2.LINE_AA,
        )

    def _request_zone_finalization(self, exit_after: bool) -> None:
        if len(self._current_points) < 3:
            self._log("Need at least three points to form a polygon.")
            return

        self._pending_zone_points = list(self._current_points)
        self._typed_name = list(f"zone-{len(self.zones) + 1}")
        self._name_dirty = False
        self._naming_active = True
        self._exit_after_save = exit_after
        self._log("Naming zone. Type to rename, Enter to confirm.")

    def _handle_naming_key(self, key: int) -> None:
        if key in {13, 10}:  # Enter
            self._commit_pending_zone()
            return

        if key in {27}:  # Esc
            self._cancel_naming()
            return

        if key in {8, 127}:  # Backspace/Delete
            if self._typed_name:
                self._typed_name.pop()
                self._name_dirty = True
            return

        if 32 <= key <= 126:
            char = chr(key)
            if not self._name_dirty and char.isprintable():
                self._typed_name = []
            if char.isprintable():
                self._typed_name.append(char)
                self._name_dirty = True

    def _commit_pending_zone(self) -> None:
        if not self._pending_zone_points:
            return

        name = "".join(self._typed_name).strip()
        if not name:
            name = f"zone-{len(self.zones) + 1}"

        color = self._palette_color(len(self.zones))
        zone = ZoneDefinition(name=name, points=list(self._pending_zone_points), color=color)
        self.zones.append(zone)

        self._current_points.clear()
        self._pending_zone_points = None
        self._naming_active = False
        self._typed_name = []
        self._name_dirty = False

        self._log(f"Zone '{name}' saved with {len(zone.points)} points.")
        self._notify_update()

        if self._exit_after_save:
            self._log("Exiting after save.")
            self._running = False

    def _cancel_naming(self) -> None:
        self._naming_active = False
        self._typed_name = []
        self._name_dirty = False
        self._pending_zone_points = None
        self._exit_after_save = False
        self._log("Zone naming cancelled. Polygon remains active.")

    def _undo_last_point(self) -> None:
        if self._current_points:
            removed = self._current_points.pop()
            self._log(f"Removed point {removed}.")
            self._notify_update()

    def _palette_color(self, index: int) -> RGBColor:
        return self.COLOR_PALETTE[index % len(self.COLOR_PALETTE)]

    def _draw_polygon(
        self,
        frame,
        points: Iterable[Point],
        color: RGBColor,
        close: bool,
        thickness: int = 1,
    ) -> None:
        pts = list(points)
        bgr = self._as_bgr(color)

        for x, y in pts:
            cv2.circle(frame, (x, y), 4, bgr, -1)

        if len(pts) < 2:
            return

        for start, end in zip(pts, pts[1:]):
            cv2.line(frame, start, end, bgr, thickness, cv2.LINE_AA)

        if close and len(pts) >= 2:
            cv2.line(frame, pts[-1], pts[0], bgr, thickness, cv2.LINE_AA)

    def _as_bgr(self, color: RGBColor) -> Tuple[int, int, int]:
        r, g, b = color
        return b, g, r

    def _current_name(self) -> str:
        return "".join(self._typed_name)

    def _notify_update(self) -> None:
        if self.on_update:
            self.on_update(self.zones)

    def _log(self, message: str) -> None:
        print(f"[polyzone] {message}")
        self._messages.push(message)
