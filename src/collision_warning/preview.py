"""Optional annotated artifacts; inference and JSONL stay in the pipeline."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from collision_warning.domain import Detection, Frame


class AnnotatedPreview:
    def __init__(self, output: Path, *, save_frames: bool, fps: float | None) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("Annotated previews require OpenCV installed") from exc
        self.cv2: Any = cv2
        self.output = output
        self.save_frames = save_frames
        self.fps = fps
        self.writer: Any = None
        self.video_shape: tuple[int, int] | None = None
        self.artifacts: list[str] = []

    def __call__(self, frame: Frame, detections: Sequence[Detection]) -> str | None:
        cv2 = self.cv2
        pixels: Any = frame.image
        annotated = pixels.copy()
        for detection in detections:
            x1, y1, x2, y2 = (int(v) for v in detection.xyxy)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (70, 220, 70), 2)
            cv2.putText(
                annotated,
                f"{detection.class_name} {detection.score:.2f}",
                (x1, max(16, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (70, 220, 70),
                2,
            )
        image_name = None
        if self.save_frames:
            image_name = f"frame-{frame.info.index:06d}.jpg"
            if not cv2.imwrite(str(self.output / image_name), annotated):
                raise OSError("Could not save annotated frame")
        if self.fps is not None:
            # MPEG-4 requires even dimensions; pad instead of cropping boxes.
            padded = cv2.copyMakeBorder(
                annotated,
                0,
                frame.info.height % 2,
                0,
                frame.info.width % 2,
                cv2.BORDER_CONSTANT,
                value=(0, 0, 0),
            )
            shape = (padded.shape[1], padded.shape[0])
            if self.writer is None:
                self.video_shape = shape
                self.writer = cv2.VideoWriter(
                    str(self.output / "detections.mp4"),
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    self.fps,
                    shape,
                )
                if not self.writer.isOpened():
                    raise OSError("Could not create annotated video")
                self.artifacts.append("detections.mp4")
            if shape != self.video_shape:
                raise ValueError("Video resolution changed during the preview")
            self.writer.write(padded)
        return image_name

    def close(self) -> None:
        if self.writer is not None:
            self.writer.release()
