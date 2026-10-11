"""Detector boundary: explicit local weights and validated original-pixel boxes."""

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any, Protocol

from collision_warning.domain import Detection, Frame


class Detector(Protocol):
    def detect(self, frame: Frame) -> Sequence[Detection]: ...

    def synchronize(self) -> None: ...


def sha256_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def verify_asset(path: Path, expected_sha256: str) -> str:
    if not path.is_file():
        raise ValueError(f"Local asset does not exist: {path}")
    expected = expected_sha256.lower()
    if len(expected) != 64 or any(v not in "0123456789abcdef" for v in expected):
        raise ValueError("Expected SHA-256 must contain 64 hexadecimal characters")
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"SHA-256 mismatch for {path.name}")
    return actual


@dataclass(frozen=True)
class DetectorConfig:
    device: str = "cpu"
    image_size: int = 640
    confidence: float = 0.1
    classes: tuple[int, ...] = (0, 1, 2, 3, 5, 7)

    def __post_init__(self) -> None:
        if self.device != "cpu" and not (
            self.device.startswith("cuda:") and self.device[5:].isdigit()
        ):
            raise ValueError("Device must be 'cpu' or 'cuda:N'")
        if self.image_size <= 0 or self.image_size % 32:
            raise ValueError("Image size must be a positive multiple of 32")
        if not isfinite(self.confidence) or not 0 < self.confidence < 1:
            raise ValueError("Confidence must be in (0, 1)")
        if not self.classes or any(v < 0 for v in self.classes):
            raise ValueError("Select at least one nonnegative class ID")


def translate_result(result: Any, frame: Frame) -> tuple[Detection, ...]:
    """Reject invalid backend results; clip finite boxes to image boundaries."""
    if tuple(result.orig_shape) != (frame.info.height, frame.info.width):
        raise ValueError("Detector result dimensions differ from the source frame")
    if result.boxes is None:
        raise ValueError("Model did not return detection boxes")
    boxes = result.boxes.cpu()
    detections = []
    for coordinates, score, category in zip(
        boxes.xyxy.tolist(), boxes.conf.tolist(), boxes.cls.tolist(), strict=True
    ):
        if not isfinite(score) or not 0 <= score <= 1:
            raise ValueError("Detector returned an invalid confidence score")
        if len(coordinates) != 4 or not all(isfinite(v) for v in coordinates):
            raise ValueError("Detector returned a malformed box")
        if not isfinite(category) or category < 0 or int(category) != category:
            raise ValueError("Detector returned an invalid class ID")
        category = int(category)
        if category not in result.names:
            raise ValueError("Detector class ID has no name")
        x1, y1, x2, y2 = coordinates
        if x1 >= x2 or y1 >= y2:
            raise ValueError("Detector returned an unordered or degenerate box")
        bounded = (
            max(0.0, min(float(x1), frame.info.width)),
            max(0.0, min(float(y1), frame.info.height)),
            max(0.0, min(float(x2), frame.info.width)),
            max(0.0, min(float(y2), frame.info.height)),
        )
        if bounded[0] == bounded[2] or bounded[1] == bounded[3]:
            continue  # Valid box entirely outside the source image.
        detections.append(
            Detection(frame.info, category, str(result.names[category]), score, bounded)
        )
    return tuple(detections)


class YoloDetector:
    def __init__(
        self, weights: Path, expected_sha256: str, config: DetectorConfig
    ) -> None:
        # Check before YOLO construction: an absent model alias must never download.
        verify_asset(weights, expected_sha256)
        if weights.suffix != ".pt":
            raise ValueError("Initial adapter supports local .pt detection weights")
        try:
            import torch
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "Use an environment with PyTorch and Ultralytics installed"
            ) from exc
        if config.device.startswith("cuda:"):
            if not torch.cuda.is_available():
                raise RuntimeError("Requested CUDA device is unavailable")
            if int(config.device[5:]) >= torch.cuda.device_count():
                raise ValueError("Requested CUDA device index does not exist")
        self.config = config
        self._torch: Any = torch
        self._model: Any = YOLO(str(weights.resolve()), task="detect")
        if self._model.task != "detect":
            raise ValueError("Selected model is not an object detector")

    def synchronize(self) -> None:
        if self.config.device.startswith("cuda:"):
            self._torch.cuda.synchronize(self.config.device)

    def detect(self, frame: Frame) -> tuple[Detection, ...]:
        results = self._model.predict(
            source=frame.image,
            device=self.config.device,
            imgsz=self.config.image_size,
            conf=self.config.confidence,
            classes=list(self.config.classes),
            rect=False,
            quantize=32,
            batch=1,
            verbose=False,
            save=False,
        )
        if len(results) != 1:
            raise ValueError("Detector must return exactly one result per frame")
        return translate_result(results[0], frame)
