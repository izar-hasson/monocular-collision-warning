"""Console entry point for the repository foundation."""

import argparse
from collections.abc import Sequence
from importlib.metadata import version


def main(argv: Sequence[str] | None = None) -> int:
    """Display help or the installed distribution's version."""
    parser = argparse.ArgumentParser(
        prog="collision-warning",
        description="Offline monocular RGB collision-warning research prototype.",
        epilog=(
            "Current status: package foundation only. "
            "Video processing arrives in Phase 1. "
            "Research use only; not a certified automotive safety system."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('monocular-collision-warning')}",
    )
    parser.parse_args(argv)
    parser.print_help()
    return 0
