"""Run boundary records failures and checks provenance before model construction."""

import json
from pathlib import Path

import pytest

import collision_warning.run as run
from collision_warning.cli import detection_test_main, main
from collision_warning.detection import DetectorConfig, sha256_file
from collision_warning.domain import Detection, Frame, FrameInfo

pytestmark = pytest.mark.integration


def assets(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    source = tmp_path / "source.mkv"
    weights = tmp_path / "weights.pt"
    source.write_bytes(b"fake source")
    weights.write_bytes(b"fake weights")
    paths = []
    for kind, asset in [("clip", source), ("model", weights)]:
        path = tmp_path / f"{kind}.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "id": kind,
                    "sha256": sha256_file(asset),
                    "source_url": "synthetic CPU fixture",
                    "license": "original fixture",
                    "permitted_use": "unit testing",
                    "split": "development",
                }
            )
        )
        paths.append(path)
    return source, weights, paths[0], paths[1]


def test_full_run_manifest_with_fake_detector(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, weights, clip, model = assets(tmp_path)

    def fake_video(*args: object):
        yield Frame(FrameInfo("clip", 0, 5, 100, 60), object())

    class FakeDetector:
        def __init__(self, *args: object) -> None:
            pass

        def synchronize(self) -> None:
            pass

        def detect(self, frame: Frame) -> tuple[Detection, ...]:
            return ()

    monkeypatch.setattr(run, "read_video", fake_video)
    monkeypatch.setattr(run, "YoloDetector", FakeDetector)
    output = tmp_path / "run"
    manifest = run.detect_video(
        source,
        weights,
        clip,
        model,
        output,
        DetectorConfig(),
        warmup_frames=5,
        max_frames=None,
    )
    assert manifest["status"] == "complete"
    assert manifest["metrics"]["frames_processed"] == 1
    assert manifest["metrics"]["latency"]["total"]["count"] == 0
    assert json.loads((output / "manifest.json").read_text())["input"][
        "sha256"
    ] == sha256_file(source)


def test_script_and_cli_produce_the_same_observations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, weights, clip, model = assets(tmp_path)

    def fake_video(path: Path, source_id: str):
        for index, timestamp in enumerate([5.0, 5.033]):
            yield Frame(FrameInfo(source_id, index, timestamp, 100, 60), object())

    class FakeDetector:
        def __init__(self, *args: object) -> None:
            pass

        def synchronize(self) -> None:
            pass

        def detect(self, frame: Frame) -> tuple[Detection, ...]:
            return (Detection(frame.info, 2, "car", 0.8, (1, 2, 20, 30)),)

    monkeypatch.setattr(run, "read_video", fake_video)
    monkeypatch.setattr(run, "YoloDetector", FakeDetector)
    arguments = [
        "--source",
        str(source),
        "--weights",
        str(weights),
        "--clip-manifest",
        str(clip),
        "--model-manifest",
        str(model),
        "--conf",
        "0.25",
        "--warmup-frames",
        "1",
        "--max-frames",
        "2",
        "--no-save-frames",
    ]
    cli_output, script_output = tmp_path / "cli", tmp_path / "script"
    assert main(["detect", *arguments, "--output", str(cli_output)]) == 0
    assert detection_test_main([*arguments, "--output", str(script_output)]) == 0
    assert (cli_output / "detections.jsonl").read_text() == (
        script_output / "detections.jsonl"
    ).read_text()
    manifests = [
        json.loads((path / "manifest.json").read_text())
        for path in [cli_output, script_output]
    ]
    assert manifests[0]["configuration"] == manifests[1]["configuration"]
    assert manifests[0]["protocol"] == manifests[1]["protocol"]
    assert all(m["metrics"]["class_counts"] == {"car": 2} for m in manifests)
    assert all(m["metrics"]["latency"]["detect"]["count"] == 1 for m in manifests)


def test_loading_failure_is_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, weights, clip, model = assets(tmp_path)

    def fail(*args: object) -> None:
        raise RuntimeError("Model loading failed")

    monkeypatch.setattr(run, "YoloDetector", fail)
    output = tmp_path / "failed-run"
    with pytest.raises(RuntimeError, match="loading failed"):
        run.detect_video(
            source,
            weights,
            clip,
            model,
            output,
            DetectorConfig(),
            warmup_frames=5,
            max_frames=None,
        )
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "failed"
    assert manifest["metrics"] is None
    assert manifest["failure"]["type"] == "RuntimeError"


def test_invalid_cuda_device_is_checked_before_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, weights, clip, model = assets(tmp_path)

    def invalid_device(*args: object) -> None:
        raise ValueError("Requested CUDA device index does not exist")

    def metadata_must_not_run(*args: object) -> None:
        raise AssertionError("Metadata queried an invalid GPU")

    monkeypatch.setattr(run, "YoloDetector", invalid_device)
    monkeypatch.setattr(run, "environment_metadata", metadata_must_not_run)
    output = tmp_path / "invalid-device"
    with pytest.raises(ValueError, match="device index does not exist"):
        run.detect_source(
            source,
            weights,
            clip,
            model,
            output,
            DetectorConfig(device="cuda:999"),
            warmup_frames=5,
            max_frames=None,
        )
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "failed"
    assert manifest["environment"] is None
    assert manifest["failure"]["type"] == "ValueError"


def test_asset_changes_fail_before_creating_output(tmp_path: Path) -> None:
    source, weights, clip, model = assets(tmp_path)
    source.write_bytes(b"modified after acquisition")
    output = tmp_path / "run"
    with pytest.raises(ValueError, match="mismatch"):
        run.detect_video(
            source,
            weights,
            clip,
            model,
            output,
            DetectorConfig(),
            warmup_frames=5,
            max_frames=None,
        )
    assert not output.exists()


def test_smoke_checksum_mismatch_preserves_output(tmp_path: Path) -> None:
    source, weights, _, _ = assets(tmp_path)
    output = tmp_path / "run"
    with pytest.raises(ValueError, match="mismatch"):
        run.detect_source(
            source,
            weights,
            None,
            None,
            output,
            DetectorConfig(),
            warmup_frames=0,
            max_frames=1,
            expected_sha256="0" * 64,
        )
    assert not output.exists()


def test_preview_failure_closes_resources_and_records_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, weights, _, _ = assets(tmp_path)
    closed = []
    detected = []

    def fake_video(*args: object):
        try:
            for index in range(2):
                yield Frame(FrameInfo(source.name, index, 5 + index, 100, 60), object())
        finally:
            closed.append("decoder")

    class FakeDetector:
        def __init__(self, *args: object) -> None:
            pass

        def synchronize(self) -> None:
            pass

        def detect(self, frame: Frame) -> tuple[Detection, ...]:
            detected.append(frame.info.index)
            return ()

    class FailingPreview:
        artifacts: list[str] = []

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __call__(self, *args: object) -> None:
            raise OSError("Preview disk full")

        def close(self) -> None:
            closed.append("preview")

    monkeypatch.setattr(run, "read_video", fake_video)
    monkeypatch.setattr(run, "YoloDetector", FakeDetector)
    monkeypatch.setattr(run, "AnnotatedPreview", FailingPreview)
    output = tmp_path / "failed-preview"
    with pytest.raises(OSError, match="disk full"):
        run.detect_source(
            source,
            weights,
            None,
            None,
            output,
            DetectorConfig(),
            warmup_frames=0,
            max_frames=2,
            save_frames=True,
        )
    assert detected == [0]  # Preview uses the existing result; no second inference.
    assert closed == ["preview", "decoder"]
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "failed"
    assert manifest["failure"]["type"] == "OSError"
