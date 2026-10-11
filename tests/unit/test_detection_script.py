"""Independent timestamp expectations and checkout-script invocation."""

import subprocess
import sys
from pathlib import Path

import pytest

from collision_warning.inputs import sequence_times

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "test_detection.py"


def test_kitti_timestamps_retain_nanoseconds_across_second_boundary(
    tmp_path: Path,
) -> None:
    timestamps = tmp_path / "timestamps.txt"
    timestamps.write_text(
        "2011-09-26 13:02:39.900000001\n"
        "2011-09-26 13:02:40.003334005\n"
        "2011-09-26 13:02:40.106665009\n"
    )
    assert sequence_times(timestamps) == [0, 0.103334004, 0.206665008]


def test_kitti_timestamp_regression_and_empty_input_fail(tmp_path: Path) -> None:
    timestamps = tmp_path / "timestamps.txt"
    timestamps.write_text("")
    with pytest.raises(ValueError, match="empty"):
        sequence_times(timestamps)
    timestamps.write_text(
        "2011-09-26 13:02:40.100000000\n2011-09-26 13:02:40.000000000\n"
    )
    with pytest.raises(ValueError, match="increase"):
        sequence_times(timestamps)


def test_script_help_works_without_gpu_packages(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert "--source" in result.stdout
    assert "--weights" in result.stdout
    assert "--device" in result.stdout
