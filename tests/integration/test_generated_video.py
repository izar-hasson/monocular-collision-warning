"""Decode a tiny generated lossless VFR video; no external media or models."""

import json
import runpy
import sys
from fractions import Fraction
from pathlib import Path

import pytest

import collision_warning.run as run
from collision_warning.video import read_video

pytestmark = [pytest.mark.integration, pytest.mark.slow]


@pytest.fixture
def generated_video(tmp_path: Path) -> Path:
    import av
    import numpy as np

    path = tmp_path / "vfr.mkv"
    pts = [5000, 5033, 5130]
    with av.open(str(path), mode="w") as container:
        stream = container.add_stream("ffv1", rate=30)
        stream.width = 32
        stream.height = 24
        stream.pix_fmt = "bgr0"
        stream.time_base = Fraction(1, 1000)
        stream.codec_context.time_base = Fraction(1, 1000)
        for i, timestamp in enumerate(pts):
            pixels = np.zeros((24, 32, 3), dtype=np.uint8)
            pixels[:, :, 0] = 10 + i
            pixels[:, :, 2] = 200
            frame = av.VideoFrame.from_ndarray(pixels, format="bgr24")
            frame.pts = timestamp
            frame.time_base = Fraction(1, 1000)
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return path


def test_generated_video_preserves_pts_and_bgr_payload(generated_video: Path) -> None:
    import numpy as np

    path = generated_video
    frames = list(read_video(path, "generated"))
    assert [f.info.timestamp_s for f in frames] == [5, 5.033, 5.13]
    assert [f.info.index for f in frames] == [0, 1, 2]
    assert all((f.info.width, f.info.height) == (32, 24) for f in frames)
    for i, decoded in enumerate(frames):
        assert decoded.image.shape == (24, 32, 3)
        assert decoded.image.dtype == np.uint8
        assert decoded.image[0, 0].tolist() == [10 + i, 0, 200]


def test_detection_script_logs_source_pts_from_real_decoder(
    generated_video: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise script orchestration with real VFR input and no model/GPU deps."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "test_detection.py"
    main = runpy.run_path(str(script), run_name="video_script_test")[
        "detection_test_main"
    ]

    class EmptyDetector:
        def __init__(self, *args: object) -> None:
            pass

        def synchronize(self) -> None:
            pass

        def detect(self, frame: object) -> list[object]:
            return []

    monkeypatch.setattr(run, "YoloDetector", EmptyDetector)
    # Headless detection should need no OpenCV import.
    monkeypatch.setitem(sys.modules, "cv2", None)
    weights = tmp_path / "weights.pt"
    weights.write_bytes(b"synthetic detector weights")
    output = tmp_path / "output"
    assert (
        main(
            [
                "--source",
                str(generated_video),
                "--weights",
                str(weights),
                "--output",
                str(output),
                "--max-frames",
                "2",
                "--warmup-frames",
                "1",
                "--no-save-frames",
            ]
        )
        == 0
    )
    records = [
        json.loads(line)
        for line in (output / "detections.jsonl").read_text().splitlines()
    ]
    assert [record["frame"]["timestamp_s"] for record in records] == [5, 5.033]
    assert all(record["detections"] == [] for record in records)
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "complete"
    assert manifest["metrics"]["frames_processed"] == 2
    assert manifest["metrics"]["latency"]["detect"]["count"] == 1
    assert [record["warmup"] for record in records] == [True, False]
    assert (
        manifest["protocol"]["timestamp_convention"]
        == "source presentation timestamp, pts * time_base"
    )
    assert manifest["input"]["provenance"] == "not supplied"


def test_missing_video_has_explicit_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="does not exist"):
        next(read_video(tmp_path / "missing.mkv", "missing"))
