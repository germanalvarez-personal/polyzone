from __future__ import annotations

import json
from pathlib import Path
import importlib.util

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("roi_tester_module", REPO_ROOT / "tools" / "roi_tester.py")
roi_tester = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None  # for type checkers
SPEC.loader.exec_module(roi_tester)


def _make_roi(tmp_path: Path) -> Path:
    roi_file = tmp_path / "roi.json"
    roi_file.write_text(
        json.dumps(
            {
                "videos": {
                    "sample": {
                        "zones": [
                            {
                                "name": "main",
                                "points": [[0, 0], [10, 0], [10, 10], [0, 10]],
                            }
                        ]
                    }
                }
            }
        )
    )
    return roi_file


def test_roi_tester_main_outputs_results(tmp_path, capsys):
    roi_file = _make_roi(tmp_path)
    roi_tester.main(
        [
            "--video",
            "sample",
            "--roi-file",
            str(roi_file),
            "--bbox",
            "0",
            "0",
            "5",
            "5",
            "--point",
            "1",
            "1",
        ]
    )

    output = capsys.readouterr().out
    assert "BBox intersects zone" in output
    assert "Point inside zone" in output


def test_roi_tester_warns_when_no_zones(tmp_path, capsys):
    empty_roi = tmp_path / "empty.json"
    empty_roi.write_text(json.dumps({"videos": {}}))
    roi_tester.main(
        [
            "--video",
            "missing",
            "--roi-file",
            str(empty_roi),
            "--bbox",
            "0",
            "0",
            "1",
            "1",
        ]
    )
    output = capsys.readouterr().out
    assert "Warning: No zones found" in output
