"""Streaming detection output and measured stage timing, independent of YOLO."""

import json
from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any

from collision_warning.detection import Detector
from collision_warning.domain import Detection, Frame, TrackingResult
from collision_warning.tracking import Tracker
from collision_warning.tracking_output import tracking_record


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
    tracker: Tracker | None = None,
    tracking_output: Path | None = None,
    tracking_preview: Callable[[Frame, TrackingResult], str | None] | None = None,
) -> dict[str, Any]:
    """Keep every observation; exclude warm-up only from warmed timing summaries."""
    if warmup_frames < 0 or (max_frames is not None and max_frames <= 0):
        raise ValueError("Warm-up must be nonnegative and frame limit positive")
    if (tracker is None) != (tracking_output is None):
        raise ValueError("Tracker and tracking output must be supplied together")
    if tracking_output is not None and tracking_output.resolve() == output.resolve():
        raise ValueError("Detection and tracking output paths must differ")
    if tracking_preview is not None and (tracker is None or preview is not None):
        raise ValueError(
            "Tracking preview requires tracking and replaces detection preview"
        )
    stages: dict[str, list[float]] = {
        "decode": [],
        "detect": [],
        "track": [],
        "preview": [],
        "serialize": [],
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
    tracking_counts: Counter[str] = Counter()
    confirmed_ids = segments = ended_tracks = 0
    peak_history = peak_retained = peak_tracks = 0
    start = perf_counter()
    with ExitStack() as stack:
        handle = stack.enter_context(output.open("x", encoding="utf-8"))
        track_handle = (
            stack.enter_context(tracking_output.open("x", encoding="utf-8"))
            if tracking_output is not None
            else None
        )
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
            track_start = perf_counter()
            tracking = (
                tracker.update(frame.info, detections) if tracker is not None else None
            )
            tracked_at = perf_counter()
            if tracking is not None:
                if (
                    tracking.frame != frame.info
                    or len(tracking.observations) != len(detections)
                    or any(
                        observation.observation_index != index
                        or observation.detection != detection
                        for index, (observation, detection) in enumerate(
                            zip(tracking.observations, detections, strict=True)
                        )
                    )
                ):
                    raise ValueError(
                        "Tracker returned observations for another frame or order"
                    )
                tracking_counts.update(o.status for o in tracking.observations)
                confirmed_ids += sum(
                    t.state == "observed" and t.observations_seen == 1
                    for t in tracking.tracks
                )
                segments += sum(
                    t.state == "observed" and t.consecutive_observations == 1
                    for t in tracking.tracks
                )
                ended_tracks += len(tracking.ended_tracks)
                peak_tracks = max(peak_tracks, len(tracking.tracks))
                peak_retained = max(
                    peak_retained, sum(len(t.history) for t in tracking.tracks)
                )
                peak_history = max(
                    peak_history,
                    max((len(t.history) for t in tracking.tracks), default=0),
                )
            class_counts.update(d.class_name for d in detections)
            row = {
                "frame": asdict(frame.info),
                "color_space": "BGR",
                "detections": [asdict(d) for d in detections],
                "warmup": count < warmup_frames,
            }
            preview_start = perf_counter()
            if tracking_preview is not None and tracking is not None:
                row["annotated_image"] = tracking_preview(frame, tracking)
            elif preview is not None:
                row["annotated_image"] = preview(frame, detections)
            preview_end = perf_counter()
            serialize_start = perf_counter()
            handle.write(json.dumps(row, allow_nan=False) + "\n")
            handle.flush()
            if track_handle is not None and tracking is not None:
                track_handle.write(
                    json.dumps(tracking_record(tracking), allow_nan=False) + "\n"
                )
                track_handle.flush()
            finished = perf_counter()
            if count == 0:
                cold_frame_s = finished - frame_start
            if count >= warmup_frames:
                if warmed_wall_start is None:
                    warmed_wall_start = frame_start
                stages["decode"].append(decoded_at - frame_start)
                stages["detect"].append(detected_at - detect_start)
                stages["track"].append(
                    tracked_at - track_start if tracking is not None else 0.0
                )
                stages["preview"].append(
                    preview_end - preview_start
                    if preview is not None or tracking_preview is not None
                    else 0.0
                )
                stages["serialize"].append(finished - serialize_start)
                stages["output"].append(finished - tracked_at)
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
        "tracking": {
            "counts": dict(tracking_counts),
            "confirmed_id_hypotheses": confirmed_ids,
            "continuity_segments": segments,
            "ended_tracks": ended_tracks,
            "peak_live_tracks": peak_tracks,
            "peak_history_observations_per_track": peak_history,
            "peak_total_retained_observations": peak_retained,
        }
        if tracker is not None
        else None,
    }
