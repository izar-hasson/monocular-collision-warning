"""Detector contracts without model weights or third-party inference imports."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from collision_warning.detection import (
    DetectorConfig,
    YoloDetector,
    sha256_file,
    translate_result,
    verify_asset,
)
from collision_warning.domain import Detection, Frame, FrameInfo


def frame() -> Frame:
    return Frame(FrameInfo("clip", 0, 12.0, 100, 60), object())


def result(rows: list[list[float]]) -> SimpleNamespace:
    boxes = SimpleNamespace(
        xyxy=SimpleNamespace(tolist=lambda: [r[:4] for r in rows]),
        conf=SimpleNamespace(tolist=lambda: [r[4] for r in rows]),
        cls=SimpleNamespace(tolist=lambda: [r[5] for r in rows]),
    )
    boxes.cpu = lambda: boxes
    return SimpleNamespace(orig_shape=(60, 100), boxes=boxes, names={2: "car"})


def test_original_pixels_class_score_and_clipping() -> None:
    detections = translate_result(result([[-2, 3, 105, 59, 0.8, 2]]), frame())
    assert detections == (Detection(frame().info, 2, "car", 0.8, (0, 3, 100, 59)),)


def test_empty_scene_and_outside_box() -> None:
    assert translate_result(result([]), frame()) == ()
    assert translate_result(result([[101, 3, 105, 59, 0.8, 2]]), frame()) == ()


@pytest.mark.parametrize(
    "row",
    [
        [1, 2, 10, 20, float("nan"), 2],
        [1, 2, 10, 20, 1.1, 2],
        [1, 2, float("inf"), 20, 0.8, 2],
        [10, 2, 1, 20, 0.8, 2],
        [1, 2, 10, 20, 0.8, 2.5],
        [1, 2, 10, 20, 0.8, 7],
    ],
)
def test_invalid_backend_observations_fail(row: list[float]) -> None:
    with pytest.raises(ValueError):
        translate_result(result([row]), frame())


def test_non_detection_model_and_wrong_dimensions() -> None:
    prediction = result([])
    prediction.boxes = None
    with pytest.raises(ValueError, match="detection boxes"):
        translate_result(prediction, frame())
    prediction = result([])
    prediction.orig_shape = (30, 50)
    with pytest.raises(ValueError, match="dimensions"):
        translate_result(prediction, frame())


def test_asset_verification_precedes_model_import(tmp_path: Path) -> None:
    weights = tmp_path / "weights.pt"
    weights.write_bytes(b"local synthetic fixture")
    assert verify_asset(weights, sha256_file(weights)) == sha256_file(weights)
    with pytest.raises(ValueError, match="mismatch"):
        YoloDetector(weights, "0" * 64, DetectorConfig())
    with pytest.raises(ValueError, match="does not exist"):
        YoloDetector(tmp_path / "yolo11n.pt", "0" * 64, DetectorConfig())
    assert "ultralytics" not in sys.modules


@pytest.mark.parametrize(
    "kwargs",
    [
        {"device": "auto"},
        {"device": "cuda:-1"},
        {"image_size": 31},
        {"confidence": float("nan")},
        {"classes": ()},
    ],
)
def test_invalid_config(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        DetectorConfig(**kwargs)
