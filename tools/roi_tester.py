"""Example script for exercising the Polyzone SDK."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from core import Polyzone


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Polyzone SDK queries against stored ROIs.")
    parser.add_argument("--video", required=True, help="Video key (or filename stem) to query.")
    parser.add_argument(
        "--roi-file",
        type=Path,
        default=Path("config/roi.json"),
        help="ROI configuration file to load.",
    )
    parser.add_argument(
        "--zone",
        default=None,
        help="Optional zone name to filter queries.",
    )
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("X1", "Y1", "X2", "Y2"),
        required=True,
        help="Bounding box coordinates for intersection tests.",
    )
    parser.add_argument(
        "--point",
        nargs=2,
        type=float,
        metavar=("X", "Y"),
        help="Optional point to evaluate with contains_point.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    sdk = Polyzone(args.video, roi_file=str(args.roi_file))
    zone_label = args.zone or "any"

    intersects = sdk.intersects_bbox(tuple(args.bbox), zone_name=args.zone)
    print(f"BBox intersects zone '{zone_label}': {intersects}")

    if args.point:
        contains = sdk.contains_point(args.point[0], args.point[1], zone_name=args.zone)
        print(f"Point inside zone '{zone_label}': {contains}")

    if not sdk.zone_names():
        print("Warning: No zones found for the provided video key.")


if __name__ == "__main__":
    main()
