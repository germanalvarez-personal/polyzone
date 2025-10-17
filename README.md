# Polyzone

Polyzone is a terminal-first toolkit for creating and managing polygon-based regions of interest (ROIs) for computer-vision workflows.

## Features
- Poetry-managed terminal tooling (`polyzone` executable) for ROI configuration management.
- OpenCV-based ROI creator that accepts still images or video clips.
- Multi-zone capture with on-screen drawing, color cycling, and named polygons.
- Export helpers for JSON, YOLO, and COCO polygon formats.

## Requirements
- Python 3.10 or later
- [Poetry](https://python-poetry.org/) for dependency management and virtual environments

## Setup
```bash
poetry install
```

This creates an isolated environment and installs the `polyzone` package along with its CLI dependencies.

## Usage
- Show help: `poetry run polyzone --help`
- Initialise a new ROI configuration (creates `config/roi.json`): `poetry run polyzone init`
- Launch the OpenCV ROI creator against an image:
  ```bash
  poetry run python tools/roi_creator.py \
    --image path/to/frame.png \
    --format json
  ```
  Controls: left-click to add points, right-click to undo the last point, `N` to store the polygon and start another, `S` to save and exit, `Q`/`Esc` to quit. Naming now happens directly inside the OpenCV window—type the label when prompted and press `Enter`. Saved polygons are annotated on the frame so the feedback stays visual.
- Add a polygon through the CLI helper:
  ```bash
  poetry run polyzone zone add \
    --video path/to/sample_video.mp4 \
    --name entrance \
    --point 10,20 \
    --point 100,20 \
    --point 100,200 \
    --point 10,200
  ```
- List stored zones: `poetry run polyzone zone list`

Use `--path` (for `init`) or `--config` (for `zone add`) to change the output location and `--force` to overwrite an existing file.
Video identifiers are normalised to their filename stem, so you can pass either the bare name (`sample_video`) or a full path (`path/to/sample_video.mp4`) when creating or listing zones.
YOLO exports require `--format yolo --image-width <w> --image-height <h>` or the ROI creator will supply dimensions automatically.

## Project Layout
```
polyzone/
├── pyproject.toml      # Poetry configuration
├── src/
│   ├── polyzone/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── cli.py
│   │   └── io/
│   │       ├── __init__.py
│   │       ├── export_formats.py
│   │       ├── roi_loader.py
│   │       └── roi_saver.py
│   └── ui/
│       ├── __init__.py
│       └── roi_creator.py
├── tools/
│   └── roi_creator.py
└── README.md
```

Future milestones (SDK, ROI loader integrations, etc.) are tracked in `.codex_tasks.json`.
