"""Command-line interface entry points."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

import click

from polyzone import get_version
from polyzone.io import load_roi, save_roi


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
MEDIA_SUFFIXES = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".mpg",
    ".mpeg",
    ".wmv",
    ".flv",
    ".webm",
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tiff",
    ".tif",
}
COLOR_CYCLE = [
    "#FF6B6B",
    "#4ECDC4",
    "#FFD166",
    "#1A535C",
    "#FF9F1C",
]


def _parse_point(raw_point: str) -> Tuple[float, float]:
    try:
        x_str, y_str = raw_point.split(",", maxsplit=1)
        return float(x_str), float(y_str)
    except ValueError as exc:
        raise click.BadParameter(
            "points must be supplied as comma-separated coordinate pairs (e.g. 10,20)"
        ) from exc


def _resolve_color(requested: str | None, existing_count: int) -> str:
    if requested:
        return requested
    return COLOR_CYCLE[existing_count % len(COLOR_CYCLE)]


def _normalize_video_key(value: str) -> str:
    """Derive the storage key used for video entries."""
    raw = value.strip()
    if any(sep in raw for sep in ("/", "\\")):
        return Path(raw).stem
    suffix = Path(raw).suffix.lower()
    if suffix in MEDIA_SUFFIXES:
        return Path(raw).stem
    return raw


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=get_version(), prog_name="polyzone")
def app() -> None:
    """Polyzone terminal interface."""


@app.command()
@click.option(
    "--path",
    "config_path",
    type=click.Path(path_type=Path),
    default=Path("config/roi.json"),
    show_default=True,
    help="Where the ROI configuration should be created.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing ROI configuration.",
)
def init(config_path: Path, force: bool) -> None:
    """Create a starter ROI configuration file."""
    target_path = config_path.expanduser().resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    default_payload = {
        "polyzone_version": get_version(),
        "videos": {},
    }

    if target_path.exists() and not force:
        click.echo(
            f"ROI configuration already exists at {target_path}. Use --force to overwrite.",
            err=True,
        )
        raise click.exceptions.Exit(code=1)

    target_path.write_text(json.dumps(default_payload, indent=2))
    click.echo(f"Created ROI configuration at {target_path}")


@app.group()
def zone() -> None:
    """Commands for managing zones."""


@zone.command()
@click.option("--video", required=True, help="Video stem to associate with the zone.")
@click.option("--name", required=True, help="Human-readable zone name.")
@click.option(
    "--point",
    "points",
    multiple=True,
    required=True,
    help="Coordinate pair defined as x,y. Repeat for each polygon vertex.",
)
@click.option("--color", default=None, help="Hex color to store with the zone.")
@click.option(
    "--format",
    "export_format",
    type=click.Choice(["json", "yolo", "coco"]),
    default="json",
    show_default=True,
    help="Export format to include with the zone definition.",
)
@click.option(
    "--image-width",
    type=float,
    default=None,
    help="Image width (required for --format yolo).",
)
@click.option(
    "--image-height",
    type=float,
    default=None,
    help="Image height (required for --format yolo).",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=Path("config/roi.json"),
    show_default=True,
    help="ROI configuration file to update.",
)
def add(
    video: str,
    name: str,
    points: Tuple[str, ...],
    color: str | None,
    export_format: str,
    image_width: float | None,
    image_height: float | None,
    config_path: Path,
) -> None:
    """Append a new polygon zone definition."""
    video_key = _normalize_video_key(video)
    parsed_points = [_parse_point(point) for point in points]
    existing_zones = load_roi(video_key, roi_file=str(config_path))
    resolved_color = _resolve_color(color, len(existing_zones))

    image_size: tuple[float, float] | None = None
    if export_format == "yolo":
        if image_width is None or image_height is None:
            raise click.UsageError("--image-width and --image-height are required for YOLO export")
        image_size = (image_width, image_height)

    entry = save_roi(
        video_stem=video_key,
        roi_entry={"name": name, "points": parsed_points, "color": resolved_color},
        output=str(config_path),
        export_format=export_format,
        image_size=image_size,
    )

    display_video = video_key if video_key == video else f"{video_key} (from {video})"
    click.echo(
        f"Added zone '{entry['name']}' ({export_format}) to video '{display_video}' in {config_path.resolve()}"
    )


@zone.command("list")
@click.option("--video", default=None, help="Filter to a single video stem.")
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=Path("config/roi.json"),
    show_default=True,
    help="ROI configuration file to read.",
)
def list_zones(video: str | None, config_path: Path) -> None:
    """List stored zones."""
    path = config_path.expanduser()
    if not path.exists():
        click.echo(f"No ROI configuration found at {path}")
        raise click.exceptions.Exit(code=1)

    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Failed to parse ROI configuration: {exc}") from exc

    videos = payload.get("videos", {})

    if video:
        normalized = _normalize_video_key(video)
        zones = videos.get(normalized, {}).get("zones", [])
        if not zones:
            label = normalized if normalized == video else f"{normalized} (from {video})"
            click.echo(f"No zones found for video '{label}'")
            return
        click.echo(f"Zones for video '{normalized}':")
        for zone in zones:
            click.echo(f"- {zone.get('name')} ({len(zone.get('points', []))} points)")
        return

    if not videos:
        click.echo("No videos stored yet.")
        return

    for video_key, entry in videos.items():
        zones = entry.get("zones", [])
        click.echo(f"{video_key}: {len(zones)} zone(s)")
