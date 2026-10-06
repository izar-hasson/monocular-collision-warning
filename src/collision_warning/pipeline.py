"""Streaming detection output and measured stage timing, independent of YOLO."""

import json
from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any

from collision_warning.detection import Detector
from collision_warning.domain import Detection, Frame


def latency_summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "p50_s": None, "p95_s": None, "mean_s": None}
    ordered = sorted(values)

    def percentile(fraction: float) -> float:
        position = (len(ordered) - 1) * fraction
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

    return {
        "count": len(values),
        "p50_s": percentile(0.5),
        "p95_s": percentile(0.95),
        "mean_s": sum(values) / len(values),
    }


def run_detection(
    frames: Iterator[Frame],
    detector: Detector,
    output: Path,
    *,
    warmup_frames: int = 5,
    max_frames: int | None = None,
    preview: Callable[[Frame, Sequence[Detection]], str | None] | None = None,
) -> dict[str, Any]:
    """Keep every observation; exclude warm-up only from warmed timing summaries."""
    if warmup_frames < 0 or (max_frames is not None and max_frames <= 0):
        raise ValueError("Warm-up must be nonnegative and frame limit positive")
    stages: dict[str, list[float]] = {
        "decode": [],
        "detect": [],
        "output": [],
        "total": [],
    }
    count = 0
    class_counts: Counter[str] = Counter()
    first: float | None = None
    last: float | None = None
    previous = None
    cold_frame_s = None
    warmed_wall_start: float | None = None
    start = perf_counter()
    with output.open("x", encoding="utf-8") as handle:
        while max_frames is None or count < max_frames:
            frame_start = perf_counter()
            try:
                frame = next(frames)
            except StopIteration:
                break
            decoded_at = perf_counter()
            if previous is not None:
                if frame.info.source_id != previous.source_id:
                    raise ValueError("Video source changed within a run")
                if frame.info.index <= previous.index:
                    raise ValueError("Frame indices did not increase")
                if frame.info.timestamp_s <= previous.timestamp_s:
                    raise ValueError("Source timestamps did not increase")
            previous = frame.info
            detector.synchronize()
            detect_start = perf_counter()
            detections = detector.detect(frame)
            detector.synchronize()
            detected_at = perf_counter()
            if any(d.frame != frame.info for d in detections):
                raise ValueError("Detector returned observations for another frame")
            class_counts.update(d.class_name for d in detections)
            row = {
                "frame": asdict(frame.info),
                "color_space": "BGR",
                "detections": [asdict(d) for d in detections],
                "warmup": count < warmup_frames,
            }
            if preview is not None:
                row["annotated_image"] = preview(frame, detections)
            handle.write(json.dumps(row, allow_nan=False) + "\n")
            handle.flush()
            finished = perf_counter()
            if count == 0:
                cold_frame_s = finished - frame_start
            if count >= warmup_frames:
                if warmed_wall_start is None:
                    warmed_wall_start = frame_start
                stages["decode"].append(decoded_at - frame_start)
                stages["detect"].append(detected_at - detect_start)
                stages["output"].append(finished - detected_at)
                stages["total"].append(finished - frame_start)
            if first is None:
                first = frame.info.timestamp_s
            last = frame.info.timestamp_s
            count += 1
    elapsed = perf_counter() - start
    warmed_elapsed = (
        perf_counter() - warmed_wall_start if warmed_wall_start is not None else None
    )
    if not count:
        raise ValueError("Video decoded no frames")
    return {
        "frames_processed": count,
        "class_counts": dict(class_counts),
        "frames_dropped": 0,
        "source_first_timestamp_s": first,
        "source_last_timestamp_s": last,
        "source_observed_rate_hz": (
            (count - 1) / (last - first)
            if first is not None and last is not None and last > first
            else None
        ),
        "elapsed_s": elapsed,
        "processed_fps_including_warmup": count / elapsed,
        "warmed_processed_fps": (
            len(stages["total"]) / warmed_elapsed
            if warmed_elapsed is not None and warmed_elapsed > 0
            else None
        ),
        "cold_first_frame_s": cold_frame_s,
        "warmup_frames_actual": min(warmup_frames, count),
        "latency": {name: latency_summary(values) for name, values in stages.items()},
    }
