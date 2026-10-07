"""Run the shared detection pipeline directly from this checkout."""
# example run:
# cd /home/izar/projects/mono-collision-risk
# ../collision-warning/.venv/bin/python scripts/test_detection.py \
#  --source data/external/kitti-0005-pyav-smoke.mkv \
#  --weights ../collision-warning/yolo11n.pt \
#  --output outputs/my-detection-test \
#  --device cuda:0 \
#  --save-video

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from collision_warning.cli import detection_test_main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(detection_test_main())
