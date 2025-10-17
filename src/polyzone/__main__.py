"""Allow running Polyzone as a module."""

from polyzone.cli import app


def main() -> None:
    """Entry point for `python -m polyzone`."""
    app()


if __name__ == "__main__":
    main()
