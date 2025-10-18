import json
from pathlib import Path

from click.testing import CliRunner

from polyzone.cli import app


def test_cli_init_and_zone_add_list():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result_init = runner.invoke(app, ["init"])
        assert result_init.exit_code == 0

        add_result = runner.invoke(
            app,
            [
                "zone",
                "add",
                "--video",
                "sample.mp4",
                "--name",
                "front",
                "--point",
                "0,0",
                "--point",
                "10,0",
                "--point",
                "10,10",
            ],
        )
        assert add_result.exit_code == 0

        list_result = runner.invoke(app, ["zone", "list", "--video", "sample.mp4"])
        assert list_result.exit_code == 0
        assert "front" in list_result.output

        payload = json.loads(Path("config/roi.json").read_text())
        assert payload["videos"]["sample"]["zones"][0]["name"] == "front"


def test_cli_zone_add_yolo_requires_dimensions():
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        result = runner.invoke(
            app,
            [
                "zone",
                "add",
                "--video",
                "sample.mp4",
                "--name",
                "front",
                "--point",
                "0,0",
                "--point",
                "10,0",
                "--point",
                "10,10",
                "--format",
                "yolo",
            ],
        )
        assert result.exit_code != 0
        assert "--image-width and --image-height are required for YOLO export" in result.output


def test_cli_zone_add_yolo_with_dimensions():
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        result = runner.invoke(
            app,
            [
                "zone",
                "add",
                "--video",
                "sample.mp4",
                "--name",
                "front",
                "--point",
                "0,0",
                "--point",
                "10,0",
                "--point",
                "10,10",
                "--format",
                "yolo",
                "--image-width",
                "100",
                "--image-height",
                "200",
            ],
        )
        assert result.exit_code == 0
        payload = json.loads(Path("config/roi.json").read_text())
        export = payload["videos"]["sample"]["zones"][0]["export"]
        assert export["format"] == "yolo"
        assert export["data"][0] == 0


def test_cli_zone_add_rejects_bad_points():
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        result = runner.invoke(
            app,
            [
                "zone",
                "add",
                "--video",
                "sample.mp4",
                "--name",
                "front",
                "--point",
                "not-a-point",
                "--point",
                "1,1",
                "--point",
                "2,2",
            ],
        )
        assert result.exit_code != 0
        assert "points must be supplied" in result.output


def test_cli_zone_list_accepts_full_path_reference():
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        runner.invoke(
            app,
            [
                "zone",
                "add",
                "--video",
                "sample.mp4",
                "--name",
                "front",
                "--point",
                "0,0",
                "--point",
                "10,0",
                "--point",
                "10,10",
            ],
        )
        result = runner.invoke(app, ["zone", "list", "--video", "videos/sample.mp4"])
        assert result.exit_code == 0
        assert "sample" in result.output


def test_cli_zone_list_requires_existing_config():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["zone", "list"])
        assert result.exit_code != 0
        assert "No ROI configuration found" in result.output


def test_cli_zone_add_requires_minimum_points():
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        result = runner.invoke(
            app,
            [
                "zone",
                "add",
                "--video",
                "sample.mp4",
                "--name",
                "front",
                "--point",
                "0,0",
                "--point",
                "10,0",
            ],
        )
        assert result.exit_code != 0
        assert "At least three points" in result.output
