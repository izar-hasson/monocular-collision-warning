"""Installed live command with real decoding/tracking and a synthetic detector."""

import json
from fractions import Fraction

import pytest

import collision_warning.run as run
from collision_warning.cli import main
from collision_warning.detection import sha256_file
from collision_warning.domain import Detection
from collision_warning.tracking import ByteTrackAdapter
from collision_warning.tracking_preview import track_preview
from collision_warning.video import read_video

pytestmark = [pytest.mark.integration, pytest.mark.tracking]


@pytest.fixture
def live_input(tmp_path, monkeypatch):
    import av
    import numpy as np

    source = tmp_path / "source.mkv"
    with av.open(str(source), "w") as container:
        stream = container.add_stream("ffv1", rate=10)
        stream.width, stream.height, stream.pix_fmt = 96, 64, "bgr0"
        stream.time_base = Fraction(1, 1000)
        stream.codec_context.time_base = stream.time_base
        for timestamp in [5000, 5100, 5200, 5300, 5400, 6600]:
            raw = av.VideoFrame.from_ndarray(
                np.zeros((64, 96, 3), dtype=np.uint8), format="bgr24"
            )
            raw.pts, raw.time_base = timestamp, Fraction(1, 1000)
            for packet in stream.encode(raw):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    weights = tmp_path / "synthetic.pt"
    weights.write_bytes(b"synthetic weights; no inference dependency")
    paths = []
    for kind, asset in [("clip", source), ("model", weights)]:
        manifest = {
            "schema_version": 1,
            "id": kind,
            "sha256": sha256_file(asset),
            "source_url": "generated:test",
            "license": "generated test fixture",
            "permitted_use": "automated tests",
            "split": "development",
        }
        path = tmp_path / f"{kind}.json"
        path.write_text(json.dumps(manifest))
        paths.append(path)

    class SyntheticDetector:
        def __init__(self, *args):
            pass

        def synchronize(self):
            pass

        def detect(self, frame):
            if frame.info.index == 3:
                return ()
            score = 0.18 if frame.info.index == 2 else 0.9
            return (Detection(frame.info, 2, "car", score, (10, 20, 50, 55)),)

    monkeypatch.setattr(run, "YoloDetector", SyntheticDetector)
    return [
        "--source",
        str(source),
        "--weights",
        str(weights),
        "--clip-manifest",
        str(paths[0]),
        "--model-manifest",
        str(paths[1]),
    ]


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_live_cli_preserves_weak_measurements_and_matches_saved_replay(
    live_input, tmp_path
):
    output = tmp_path / "tracked"
    assert (
        main(
            [
                "track",
                *live_input,
                "--output",
                str(output),
                "--warmup-frames",
                "2",
                "--save-video",
                "--save-frames",
                "--history-max-observations",
                "2",
            ]
        )
        == 0
    )
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "complete"
    assert manifest["metrics"]["frames_processed"] == 6
    for stage in ["detect", "track", "preview", "serialize", "total"]:
        assert manifest["metrics"]["latency"][stage]["count"] == 4
    assert manifest["metrics"]["latency"]["track"]["p95_s"] > 0
    assert manifest["tracking"]["history_max_observations"] == 2
    assert manifest["tracking"]["frame_rate"] == 10
    measured = rows(output / "detections.jsonl")
    tracked = rows(output / "tracks.jsonl")
    assert measured[2]["detections"][0]["score"] == 0.18
    for original, associated in zip(measured, tracked, strict=True):
        assert original["detections"] == [
            o["detection"] for o in associated["observations"]
        ]
    assert tracked[3]["observations"] == []
    assert tracked[3]["tracks"][0]["state"] == "lost"
    assert tracked[4]["observations"][0]["segment_id"] == 1
    assert tracked[5]["reset_reason"] == "time_gap"
    assert all(t["history_size"] <= 2 for row in tracked for t in row["tracks"])
    assert len(list(output.glob("frame-*.jpg"))) == 6
    video = list(read_video(output / "tracking.mp4", "preview"))
    assert [f.info.timestamp_s for f in video] == pytest.approx(
        [0, 0.1, 0.2, 0.3, 0.4, 1.6], abs=1e-6
    )
    for name, expected in manifest["artifact_sha256"].items():
        assert sha256_file(output / name) == expected
    replay = tmp_path / "replay"
    track_preview(tmp_path / "source.mkv", output, replay)
    for direct, offline in zip(tracked, rows(replay / "tracks.jsonl"), strict=True):
        assert [(o["backend_id"], o["segment_id"]) for o in direct["observations"]] == [
            (o["backend_id"], o["segment_id"]) for o in offline["observations"]
        ]


def test_matched_headless_modes_share_detections_and_separate_tracking_cost(
    live_input, tmp_path
):
    for command in ["detect", "track"]:
        assert (
            main(
                [
                    command,
                    *live_input,
                    "--output",
                    str(tmp_path / command),
                    "--warmup-frames",
                    "1",
                ]
            )
            == 0
        )
    baseline = json.loads((tmp_path / "detect/manifest.json").read_text())
    tracked = json.loads((tmp_path / "track/manifest.json").read_text())
    assert baseline["metrics"]["latency"]["track"]["p50_s"] == 0
    assert tracked["metrics"]["latency"]["track"]["p50_s"] > 0
    assert baseline["metrics"]["latency"]["preview"]["p50_s"] == 0
    assert tracked["metrics"]["latency"]["preview"]["p50_s"] == 0
    assert (tmp_path / "detect/detections.jsonl").read_bytes() == (
        tmp_path / "track/detections.jsonl"
    ).read_bytes()
    assert not (tmp_path / "detect/tracks.jsonl").exists()
    assert not list((tmp_path / "track").glob("*.mp4"))


def test_detector_floor_incompatible_with_tracking_is_rejected_before_output(
    live_input, tmp_path, capsys
):
    output = tmp_path / "bad-floor"
    with pytest.raises(SystemExit) as exc:
        main(["track", *live_input, "--output", str(output), "--conf", ".25"])
    assert exc.value.code == 1
    assert "Detector confidence" in capsys.readouterr().err
    assert not output.exists()


def test_tracking_failure_marks_manifest_failed_and_closes_partial_video(
    live_input, tmp_path, monkeypatch
):
    original = ByteTrackAdapter.update

    def fail(self, frame, observations):
        if frame.index == 2:
            raise RuntimeError("synthetic tracking failure")
        return original(self, frame, observations)

    monkeypatch.setattr(ByteTrackAdapter, "update", fail)
    output = tmp_path / "failed"
    with pytest.raises(SystemExit) as exc:
        main(["track", *live_input, "--output", str(output), "--save-video"])
    assert exc.value.code == 1
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "failed"
    assert manifest["failure"]["message"] == "synthetic tracking failure"
    assert "artifact_sha256" not in manifest
    assert len(rows(output / "tracks.jsonl")) == 2
    assert len(list(read_video(output / "tracking.mp4", "partial"))) == 2
