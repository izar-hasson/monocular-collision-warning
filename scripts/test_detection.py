"""Run the shared detection pipeline directly from this checkout."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from collision_warning.cli import detection_test_main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(detection_test_main())
