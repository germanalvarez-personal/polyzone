"""Command-line interface for the OpenCV-based ROI creator."""

from __future__ import annotations

import argparse
from pathlib import Path

from polyzone.io import save_roi
from ui.roi_creator import ROICreator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the Polyzone ROI creator UI.")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--image", type=Path, help="Path to an image file to annotate.")
    source_group.add_argument("--video", type=Path, help="Path to a video file to annotate.")
    parser.add_argument(
        "--format",
        choices=["json", "yolo", "coco"],
        default="json",
        help="Export format for saved polygons.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("config/roi.json"),
        help="ROI configuration file to update.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_path: Path = args.image or args.video
    video_stem = input_path.stem

    creator = ROICreator(input_path=input_path, export_format=args.format)
    zones = creator.start()

    if not zones:
        print("No zones were created. Exiting without changes.")
        return

    image_size = (float(creator.width), float(creator.height))

    for zone in zones:
        save_roi(
            video_stem=video_stem,
            roi_entry={"name": zone.name, "points": zone.points, "color": zone.color},
            output=str(args.output),
            export_format=args.format,
            image_size=image_size if args.format == "yolo" else None,
        )

    print(f"Saved {len(zones)} zone(s) for '{video_stem}' to {args.output.resolve()}")


if __name__ == "__main__":
    main()
