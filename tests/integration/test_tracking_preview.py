"""Real CPU association, encoding and playback without models or external media."""

import json
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path

import pytest

from collision_warning.cli import main
from collision_warning.detection import sha256_file
from collision_warning.domain import Detection, FrameInfo
from collision_warning.tracking_preview import PreviewTrackingConfig, track_preview
from collision_warning.video import read_video

pytestmark = [pytest.mark.integration, pytest.mark.tracking]


@pytest.fixture
def saved_run(tmp_path: Path):
    import av
    import numpy as np

    source = tmp_path / "source.mkv"
    timestamps = [5000, 5100, 5200, 5400, 5600, 6800]
    with av.open(str(source), "w") as container:
        stream = container.add_stream("ffv1", rate=10)
        stream.width, stream.height, stream.pix_fmt = 160, 95, "bgr0"
        stream.time_base = Fraction(1, 1000)
        stream.codec_context.time_base = stream.time_base
        for timestamp in timestamps:
            raw = av.VideoFrame.from_ndarray(
                np.zeros((95, 160, 3), dtype=np.uint8), format="bgr24"
            )
            raw.pts, raw.time_base = timestamp, Fraction(1, 1000)
            for packet in stream.encode(raw):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    run = tmp_path / "detections"
    run.mkdir()
    manifest = {
        "schema_version": 1,
        "status": "complete",
        "input": {"id": "generated", "sha256": sha256_file(source)},
        "metrics": {"frames_processed": len(timestamps)},
    }
    (run / "manifest.json").write_text(json.dumps(manifest))
    rows = []
    for index, timestamp in enumerate(timestamps):
        frame = FrameInfo("generated", index, timestamp / 1000, 160, 95)
        score = 0.18 if index == 2 else 0.9
        detections = (
            []
            if index == 3
            else [
                Detection(frame, 2, "car", score, (8, 40, 38, 75)),
                Detection(frame, 0, "person", score, (90, 40, 120, 75)),
            ]
        )
        if index == 2:
            detections.append(Detection(frame, 1, "bicycle", 0.05, (55, 40, 75, 75)))
        rows.append(
            {
                "frame": asdict(frame),
                "color_space": "BGR",
                "detections": [asdict(d) for d in detections],
            }
        )
    write_rows(run, rows)
    return source, run, json.loads(json.dumps(rows))


def write_rows(run, rows):
    (run / "detections.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows)
    )


def test_cli_encodes_measured_ids_empty_frames_and_original_intervals(
    saved_run, tmp_path, monkeypatch
):
    import cv2
    import numpy as np

    source, run, original = saved_run
    source_hash, detection_hash = (
        sha256_file(source),
        sha256_file(run / "detections.jsonl"),
    )
    output = tmp_path / "preview"
    labels = []
    put_text = cv2.putText

    def record_text(image, text, *args, **kwargs):
        labels.append(text)
        return put_text(image, text, *args, **kwargs)

    monkeypatch.setattr(cv2, "putText", record_text)
    assert (
        main(
            [
                "track-preview",
                "--source",
                str(source),
                "--detection-run",
                str(run),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "complete"
    assert manifest["frames_processed"] == 6
    assert manifest["counts"] == {
        "associated": 6,
        "unassigned": 4,
        "below_floor": 1,
        "low_score_associated": 2,
    }
    assert manifest["input"]["sha256"] == source_hash == sha256_file(source)
    assert (
        manifest["detections_sha256"]
        == detection_hash
        == sha256_file(run / "detections.jsonl")
    )
    for name, metadata in manifest["artifacts"].items():
        assert sha256_file(output / name) == metadata["sha256"]
    records = [
        json.loads(line) for line in (output / "tracks.jsonl").read_text().splitlines()
    ]
    for before, after in zip(original, records, strict=True):
        assert before["frame"] == after["frame"]
        assert before["detections"] == [o["detection"] for o in after["observations"]]
        assert [o["observation_index"] for o in after["observations"]] == list(
            range(len(before["detections"]))
        )
    car = records[1]["observations"][0]
    person = records[1]["observations"][1]
    assert car["track_id"] != person["track_id"]  # Both backends allocate ID zero.
    assert car["backend_id"] == person["backend_id"] == 0
    assert records[2]["observations"][0]["track_id"] == car["track_id"]
    assert records[4]["observations"][0]["track_id"] == car["track_id"]
    assert records[3]["observations"] == []
    assert all(t["state"] == "lost" for t in records[3]["tracks"])
    assert records[2]["observations"][0]["segment_id"] == 0
    assert records[4]["observations"][0]["segment_id"] == 1
    assert all(t["history_size"] == 1 for t in records[4]["tracks"])
    assert records[5]["reset_reason"] == "time_gap"
    assert {t["track_id"] for t in records[5]["ended_tracks"]} == {
        car["track_id"],
        person["track_id"],
    }
    assert all(o["track_id"] is None for o in records[5]["observations"])
    assert "car #2:0 0.18" in labels
    assert "bicycle unassigned 0.05" in labels
    assert "person #0:0 0.90" in labels
    decoded = list(read_video(output / "tracking.mp4", "preview"))
    assert len(decoded) == 6
    assert all((f.info.width, f.info.height) == (160, 96) for f in decoded)
    assert [f.info.timestamp_s for f in decoded] == pytest.approx(
        [0, 0.1, 0.2, 0.4, 0.6, 1.8], abs=1e-6
    )
    assert np.any(decoded[1].image[40:75, 8:39])  # Actual boxes were encoded.
    assert np.max(decoded[3].image) < 5  # Empty frame has no predicted boxes.
    assert np.max(list(read_video(source, "generated"))[1].image) == 0


@pytest.mark.parametrize(
    "mutation",
    ["timestamp", "source_id", "dimensions", "box", "nan", "extra", "missing"],
)
def test_bad_records_fail_without_claiming_a_complete_preview(
    saved_run, tmp_path, mutation
):
    source, run, rows = saved_run
    if mutation == "timestamp":
        rows[1]["frame"]["timestamp_s"] = 5.0
    elif mutation == "source_id":
        rows[1]["frame"]["source_id"] = "another-source"
    elif mutation == "dimensions":
        rows[1]["frame"]["width"] = 159
    elif mutation == "box":
        rows[1]["detections"][0]["xyxy"][2] = 1000
    elif mutation == "nan":
        rows[1]["detections"][0]["score"] = float("nan")
    elif mutation == "extra":
        rows.append(rows[-1])
    else:
        rows.pop()
    write_rows(run, rows)
    output = tmp_path / "failed"
    with pytest.raises(ValueError):
        track_preview(source, run, output)
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "failed"
    assert manifest["failure"]["type"] == "ValueError"
    assert manifest["artifacts"] == {}


def test_source_checksum_and_existing_output_rejected(saved_run, tmp_path):
    source, run, _ = saved_run
    existing = tmp_path / "existing"
    existing.mkdir()
    sentinel = existing / "keep.txt"
    sentinel.write_text("keep")
    with pytest.raises(ValueError, match="already exists"):
        track_preview(source, run, existing)
    assert sentinel.read_text() == "keep"
    wrong = tmp_path / "wrong.mkv"
    wrong.write_bytes(source.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="SHA-256"):
        track_preview(wrong, run, tmp_path / "wrong-output")
    assert not (tmp_path / "wrong-output").exists()


def test_detection_prefix_is_supported(saved_run, tmp_path):
    source, run, rows = saved_run
    manifest = json.loads((run / "manifest.json").read_text())
    manifest["metrics"]["frames_processed"] = 3
    (run / "manifest.json").write_text(json.dumps(manifest))
    write_rows(run, rows[:3])
    assert track_preview(source, run, tmp_path / "prefix")["frames_processed"] == 3


@pytest.mark.parametrize(
    "options",
    [
        {"low_score": 0.7},
        {"high_score": 0.7},
        {"activation_score": 1.1},
        {"lost_seconds": 0},
        {"minimum_iou": -1},
        {"low_score": float("nan")},
    ],
)
def test_invalid_configuration_is_rejected(options):
    with pytest.raises(ValueError):
        PreviewTrackingConfig(**options)
