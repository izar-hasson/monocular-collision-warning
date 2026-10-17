"""CPU association and timestamped video previews from saved detection runs.

This tool renders shared adapter results. It computes no motion or risk estimate.
"""

import json
from collections import Counter
from contextlib import ExitStack
from dataclasses import asdict, replace
from datetime import UTC, datetime
from fractions import Fraction
from importlib.metadata import version
from math import isfinite
from pathlib import Path
from typing import Any
from uuid import uuid4

from collision_warning.detection import sha256_file, verify_asset
from collision_warning.domain import Detection, Frame, FrameInfo, TrackingResult
from collision_warning.run import code_metadata
from collision_warning.tracking import ByteTrackAdapter, TrackingConfig
from collision_warning.tracking_output import tracking_record
from collision_warning.video import read_video, video_properties

PreviewTrackingConfig = TrackingConfig  # Compatibility for the initial preview API.


def parse_observations(line: str, frame: FrameInfo) -> list[Detection]:
    """Reject mismatched frames and invalid measurements before association."""
    try:
        row = json.loads(line)
        if row["frame"] != asdict(frame) or row["color_space"] != "BGR":
            raise ValueError("Saved detections do not match the decoded source frame")
        if not isinstance(row["detections"], list):
            raise ValueError("Saved detections must be a list")
        observations = []
        for item in row["detections"]:
            if item["frame"] != row["frame"]:
                raise ValueError("Detection refers to a different frame")
            if type(item["class_id"]) is not int:
                raise ValueError("Detection class ID must be an integer")
            if not isinstance(item["class_name"], str):
                raise ValueError("Detection class name must be a string")
            box = item["xyxy"]
            if not isinstance(box, list) or len(box) != 4:
                raise ValueError("Detection box must contain four coordinates")
            observations.append(
                Detection(
                    frame,
                    item["class_id"],
                    item["class_name"],
                    float(item["score"]),
                    (float(box[0]), float(box[1]), float(box[2]), float(box[3])),
                )
            )
        return observations
    except (KeyError, TypeError, OverflowError) as exc:
        raise ValueError("Invalid saved detection record") from exc


def draw_tracks(
    frame: Frame,
    observations: list[Detection],
    ids: list[int | None],
    *,
    epoch: int = 0,
) -> Any:
    """Render only current measured boxes, with gray unassigned observations."""
    import cv2

    pixels: Any = frame.image
    annotated = pixels.copy()
    # Draw confirmed labels last so overlapping unassigned boxes cannot hide IDs.
    ordered = sorted(
        zip(observations, ids, strict=True), key=lambda item: item[1] is not None
    )
    for detection, identity in ordered:
        if identity is None:
            color = (160, 160, 160)
            label = f"{detection.class_name} unassigned {detection.score:.2f}"
        else:
            # Stable per-class colors; backend numbers alone are not unique.
            seed = (detection.class_id + 1) * 1009 + identity * 9176 + epoch * 7919
            color = (
                64 + seed % 192,
                64 + ((seed >> 5) % 192),
                64 + ((seed >> 10) % 192),
            )
            label = (
                f"{detection.class_name} #"
                f"{'e' + str(epoch) + '/' if epoch else ''}"
                f"{detection.class_id}:{identity} "
                f"{detection.score:.2f}"
            )
        x1, y1, x2, y2 = (int(v) for v in detection.xyxy)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        x = max(0, min(x1, frame.info.width - size[0] - 4))
        y = max(size[1] + 4, y1 - 4)
        cv2.rectangle(
            annotated,
            (x, y - size[1] - 3),
            (x + size[0] + 3, y + baseline),
            (0, 0, 0),
            -1,
        )
        cv2.putText(
            annotated, label, (x + 1, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1
        )
    return annotated


class TimestampedPreview:
    """H.264 MP4 with original frame intervals and a zero-based playback clock."""

    def __init__(self, path: Path, first: FrameInfo, fps: float) -> None:
        import av

        self.av: Any = av
        self.container: Any = av.open(str(path), mode="w")
        try:
            self.stream: Any = self.container.add_stream(
                "libx264", rate=Fraction(fps).limit_denominator(100000)
            )
            self.stream.width = first.width + first.width % 2
            self.stream.height = first.height + first.height % 2
            self.stream.pix_fmt = "yuv420p"
            self.stream.time_base = Fraction(1, 1000000)
            self.stream.codec_context.time_base = self.stream.time_base
            self.stream.options = {"crf": "18", "preset": "fast"}
        except Exception:
            self.container.close()
            raise
        self.origin = first.timestamp_s
        self.previous_pts = -1
        self.closed = False

    def write(self, frame: Frame, pixels: Any) -> None:
        import cv2

        if (
            frame.info.width + frame.info.width % 2 != self.stream.width
            or frame.info.height + frame.info.height % 2 != self.stream.height
        ):
            raise ValueError("Video resolution changed during tracking preview")
        pts = round((frame.info.timestamp_s - self.origin) * 1000000)
        if pts <= self.previous_pts:
            raise ValueError(
                "Frame timestamps collide at microsecond preview precision"
            )
        self.previous_pts = pts
        padded = cv2.copyMakeBorder(
            pixels,
            0,
            frame.info.height % 2,
            0,
            frame.info.width % 2,
            cv2.BORDER_CONSTANT,
            value=(0, 0, 0),
        )
        raw = self.av.VideoFrame.from_ndarray(padded, format="bgr24")
        raw.pts = pts
        raw.time_base = Fraction(1, 1000000)
        for packet in self.stream.encode(raw):
            self.container.mux(packet)

    def close(self) -> None:
        if not self.closed:
            self.closed = True
            try:
                for packet in self.stream.encode():
                    self.container.mux(packet)
            finally:
                self.container.close()


class TrackingAnnotatedPreview:
    """Measured track overlay shared by live inference and saved detections."""

    def __init__(self, output: Path, *, save_frames: bool, fps: float | None) -> None:
        self.output = output
        self.save_frames = save_frames
        self.fps = fps
        self.writer: TimestampedPreview | None = None
        self.artifacts: list[str] = []

    def __call__(self, frame: Frame, result: TrackingResult) -> str | None:
        import cv2

        observations = [o.detection for o in result.observations]
        ids = [
            o.identity.backend_id if o.identity else None for o in result.observations
        ]
        epoch = next((o.identity.epoch for o in result.observations if o.identity), 0)
        pixels = draw_tracks(frame, observations, ids, epoch=epoch)
        image_name = None
        if self.save_frames:
            image_name = f"frame-{frame.info.index:06d}.jpg"
            if not cv2.imwrite(str(self.output / image_name), pixels):
                raise OSError("Could not save annotated tracking frame")
        if self.fps is not None:
            if self.writer is None:
                self.writer = TimestampedPreview(
                    self.output / "tracking.mp4", frame.info, self.fps
                )
                self.artifacts.append("tracking.mp4")
            self.writer.write(frame, pixels)
        return image_name

    def close(self) -> None:
        if self.writer is not None:
            self.writer.close()


def track_preview(
    source: Path,
    detection_run: Path,
    output: Path,
    config: PreviewTrackingConfig | None = None,
) -> dict[str, Any]:
    """Replay a completed detection run against its checksum-verified video."""
    config = config or PreviewTrackingConfig()
    if output.exists():
        raise ValueError("Output directory already exists; choose a new run directory")
    run_path = detection_run / "manifest.json"
    detections_path = detection_run / "detections.jsonl"
    original = json.loads(run_path.read_text(encoding="utf-8"))
    try:
        if original["schema_version"] != 1 or original["status"] != "complete":
            raise ValueError("A completed version-1 detection run is required")
        clip = original["input"]
        source_id = clip["id"]
        expected_count = original["metrics"]["frames_processed"]
        if not isinstance(source_id, str) or not source_id:
            raise ValueError("Detection run requires a source ID")
        if type(expected_count) is not int or expected_count <= 0:
            raise ValueError("Detection run requires a positive processed frame count")
        verify_asset(source, clip["sha256"])
    except (KeyError, TypeError) as exc:
        raise ValueError("Invalid detection run manifest") from exc
    detections_hash = sha256_file(detections_path)
    fps = video_properties(source)["nominal_fps"]
    if not isfinite(fps) or fps <= 0:
        raise ValueError("Preview requires a positive nominal video rate")
    config = replace(config, frame_rate=fps)
    namespace = uuid4().hex
    tracker = ByteTrackAdapter(config, namespace=namespace)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "status": "running",
        "started_at_utc": datetime.now(UTC).isoformat(),
        "input": clip,
        "source": str(source),
        "detection_run": str(detection_run),
        "detection_manifest_sha256": sha256_file(run_path),
        "detections_sha256": detections_hash,
        "code": code_metadata(),
        "configuration": {
            **asdict(config),
            "minimum_consecutive_frames": 2,
            "frame_rate": fps,
            "lost_track_buffer": config.lost_track_buffer,
            "effective_lost_seconds": config.effective_lost_seconds,
        },
        "identity_namespace": namespace,
        "identity_format": "namespace/epoch/class_id/backend_id",
        "history_policy": "Current continuity segment; bounded by count and source age",
        "packages": {
            p: version(p) for p in ("trackers", "supervision", "av", "opencv-python")
        },
        "frames_processed": 0,
        "counts": {},
        "artifacts": {},
        "failure": None,
        "limitations": [
            "Association preview only; IDs are unverified identity hypotheses.",
            "Per-class association can fragment IDs when the detector changes class.",
            "Only original observed boxes are drawn; histories contain no predictions.",
            "Gaps start new history segments; IDs remain unverified hypotheses.",
            "No TTC, distance or collision-risk evaluation; source audio is omitted.",
            "Playback starts at zero; source intervals are retained to microseconds.",
            "Odd dimensions are padded at right/bottom; coordinates are unchanged.",
            "Input is the processed video prefix recorded by the detection run.",
            "Detections removed during inference cannot be recovered by tracking.",
        ],
    }
    output.mkdir(parents=True)
    counts: Counter[str] = Counter()
    try:
        with ExitStack() as stack:
            frames = read_video(source, source_id)
            stack.callback(frames.close)
            rows = stack.enter_context(detections_path.open(encoding="utf-8"))
            results = stack.enter_context(
                (output / "tracks.jsonl").open("x", encoding="utf-8")
            )
            writer = None
            for index, line in enumerate(rows):
                if index >= expected_count:
                    raise ValueError("Detection rows exceed the recorded frame count")
                frame = next(frames, None)
                if frame is None:
                    raise ValueError("Source video ends before saved detections")
                observations = parse_observations(line, frame.info)
                tracking = tracker.update(frame.info, observations)
                ids = [
                    o.identity.backend_id if o.identity is not None else None
                    for o in tracking.observations
                ]
                if writer is None:
                    writer = TimestampedPreview(
                        output / "tracking.mp4", frame.info, fps
                    )
                    stack.callback(writer.close)
                epoch = next(
                    (o.identity.epoch for o in tracking.observations if o.identity), 0
                )
                writer.write(frame, draw_tracks(frame, observations, ids, epoch=epoch))
                for observation in tracking.observations:
                    counts[observation.status] += 1
                    if (
                        observation.identity is not None
                        and observation.detection.score < config.high_score
                    ):
                        counts["low_score_associated"] += 1
                results.write(
                    json.dumps(tracking_record(tracking), allow_nan=False) + "\n"
                )
                manifest["frames_processed"] += 1
            if manifest["frames_processed"] != expected_count:
                raise ValueError("Detection rows do not match the recorded frame count")
        for name in ("tracking.mp4", "tracks.jsonl"):
            manifest["artifacts"][name] = {"sha256": sha256_file(output / name)}
        manifest["status"] = "complete"
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        manifest["counts"] = dict(counts)
        (output / "manifest.json").write_text(
            json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
    return manifest
