"""Actual JSONL, temporal ordering and failure behavior using a fake detector."""

import json
from pathlib import Path

import pytest

from collision_warning.domain import Detection, Frame, FrameInfo
from collision_warning.pipeline import latency_summary, run_detection
from collision_warning.run import read_asset_manifest

pytestmark = pytest.mark.integration


class FakeDetector:
    def synchronize(self) -> None:
        pass

    def detect(self, frame: Frame) -> tuple[Detection, ...]:
        if frame.info.index == 1:
            return ()
        return (Detection(frame.info, 2, "car", 0.8, (1, 2, 20, 30)),)


def frames() -> list[Frame]:
    return [
        Frame(FrameInfo("clip", i, t, 100, 60), object())
        for i, t in enumerate([5.0, 5.033, 5.13])
    ]


def test_streamed_observations_and_warmup_accounting(tmp_path: Path) -> None:
    output = tmp_path / "detections.jsonl"
    metrics = run_detection(iter(frames()), FakeDetector(), output, warmup_frames=1)
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert [r["frame"]["timestamp_s"] for r in rows] == [5.0, 5.033, 5.13]
    assert rows[1]["detections"] == []
    assert [r["warmup"] for r in rows] == [True, False, False]
    assert metrics["frames_processed"] == 3
    assert metrics["latency"]["detect"]["count"] == 2
    assert metrics["source_observed_rate_hz"] == pytest.approx(2 / 0.13)
    assert metrics["warmed_processed_fps"] > 0
    assert "risk" not in rows[0]


def test_limit_does_not_consume_extra_frames_or_invent_warmed_metrics(
    tmp_path: Path,
) -> None:
    stream = iter(frames())
    metrics = run_detection(stream, FakeDetector(), tmp_path / "rows", max_frames=1)
    assert next(stream).info.index == 1
    assert metrics["source_observed_rate_hz"] is None
    assert metrics["warmed_processed_fps"] is None
    assert metrics["latency"]["total"]["p95_s"] is None


def test_empty_source_fails_and_existing_output_is_preserved(tmp_path: Path) -> None:
    output = tmp_path / "rows"
    with pytest.raises(ValueError, match="no frames"):
        run_detection(iter(()), FakeDetector(), output)
    output.write_text("existing result")
    with pytest.raises(FileExistsError):
        run_detection(iter(frames()), FakeDetector(), output)
    assert output.read_text() == "existing result"


def test_pipeline_rejects_wrong_frame_and_reordered_input(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="indices"):
        run_detection(iter(frames()[::-1]), FakeDetector(), tmp_path / "backward")

    class WrongDetector(FakeDetector):
        def detect(self, frame: Frame) -> tuple[Detection, ...]:
            return (
                Detection(
                    FrameInfo("other", 0, 0, 100, 60), 2, "car", 1, (1, 2, 20, 30)
                ),
            )

    with pytest.raises(ValueError, match="another frame"):
        run_detection(iter(frames()), WrongDetector(), tmp_path / "wrong")


def test_latency_percentiles_have_known_answers() -> None:
    summary = latency_summary([4, 1, 3, 2])
    assert summary["p50_s"] == 2.5
    assert summary["p95_s"] == pytest.approx(3.85)
    assert summary["mean_s"] == 2.5
    assert latency_summary([])["p50_s"] is None


def test_missing_provenance_cannot_be_treated_as_reviewed(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text('{"schema_version": 1, "status": "template"}')
    with pytest.raises(ValueError, match="requires"):
        read_asset_manifest(path, "clip")
