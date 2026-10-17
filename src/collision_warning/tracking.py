"""Independent CPU tracking adapter and bounded, measurement-only histories."""

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from typing import Any, Protocol
from uuid import uuid4

from collision_warning.domain import (
    Detection,
    FrameInfo,
    Track,
    TrackedDetection,
    TrackEnd,
    TrackEndReason,
    TrackIdentity,
    TrackingResult,
)


@dataclass(frozen=True)
class TrackingConfig:
    low_score: float = 0.1
    high_score: float = 0.5
    activation_score: float = 0.6
    minimum_iou: float = 0.3
    lost_seconds: float = 1.0
    frame_rate: float = 10.0
    max_gap_seconds: float = 1.0
    history_max_observations: int = 30
    history_max_seconds: float = 2.0

    def __post_init__(self) -> None:
        values = (
            self.low_score,
            self.high_score,
            self.activation_score,
            self.minimum_iou,
            self.lost_seconds,
            self.frame_rate,
            self.max_gap_seconds,
            self.history_max_seconds,
        )
        if not all(isfinite(v) for v in values):
            raise ValueError("Tracking parameters must be finite")
        if not 0 <= self.low_score <= self.high_score <= self.activation_score <= 1:
            raise ValueError("Require 0 <= low <= high <= activation <= 1")
        if not 0 <= self.minimum_iou <= 1 or self.lost_seconds < 1 / 30:
            raise ValueError("Require IoU in [0, 1] and lost buffer >= 1/30 second")
        if self.frame_rate <= 0 or self.max_gap_seconds <= 0:
            raise ValueError("Frame rate and maximum source-time gap must be positive")
        if (
            type(self.history_max_observations) is not int
            or self.history_max_observations <= 0
        ):
            raise ValueError("History observation limit must be a positive integer")
        if self.history_max_seconds <= 0:
            raise ValueError("History time limit must be positive")

    @property
    def lost_track_buffer(self) -> int:
        return round(self.lost_seconds * 30)

    @property
    def effective_lost_seconds(self) -> float:
        return self.lost_track_buffer / 30


class Tracker(Protocol):
    def update(
        self, frame: FrameInfo, detections: Sequence[Detection]
    ) -> TrackingResult: ...

    def reset(self) -> tuple[TrackEnd, ...]: ...


class ObservationHistory:
    """Retain original detections, never frames/pixels, bounded by count and time."""

    def __init__(self, config: TrackingConfig) -> None:
        self._items: deque[Detection] = deque(maxlen=config.history_max_observations)
        self._seconds = config.history_max_seconds
        self._previous: tuple[FrameInfo, int] | None = None
        self._clock: float | None = None

    @property
    def observations(self) -> tuple[Detection, ...]:
        return tuple(self._items)

    def append(self, detection: Detection) -> None:
        if not isinstance(detection.xyxy, tuple):
            raise ValueError("History requires immutable detection coordinates")
        previous = self._previous
        if previous is not None and (
            detection.frame.source_id != previous[0].source_id
            or detection.class_id != previous[1]
            or (detection.frame.width, detection.frame.height)
            != (previous[0].width, previous[0].height)
            or detection.frame.index <= previous[0].index
            or detection.frame.timestamp_s <= previous[0].timestamp_s
        ):
            raise ValueError(
                "History requires increasing measurements of one class/source"
            )
        if self._clock is not None and detection.frame.timestamp_s < self._clock:
            raise ValueError("History measurement predates its pruning clock")
        self.prune(detection.frame.timestamp_s)
        self._items.append(detection)
        self._previous = (detection.frame, detection.class_id)

    def prune(self, timestamp_s: float) -> None:
        if not isfinite(timestamp_s) or (
            self._clock is not None and timestamp_s < self._clock
        ):
            raise ValueError("History pruning time must be finite and nondecreasing")
        cutoff = timestamp_s - self._seconds
        while self._items and self._items[0].frame.timestamp_s < cutoff:
            self._items.popleft()
        self._clock = timestamp_s

    def clear(self) -> None:
        self._items.clear()
        self._previous = None
        self._clock = None


@dataclass
class _LiveTrack:
    identity: TrackIdentity
    history: ObservationHistory
    first_timestamp_s: float
    last_frame: FrameInfo
    segment_id: int = 0
    observations_seen: int = 0
    consecutive_observations: int = 0

    def observe(self, detection: Detection) -> None:
        if (
            self.observations_seen
            and detection.frame.index != self.last_frame.index + 1
        ):
            self.segment_id += 1
            self.consecutive_observations = 0
            self.history.clear()
        self.history.append(detection)
        self.last_frame = detection.frame
        self.observations_seen += 1
        self.consecutive_observations += 1

    def snapshot(self, frame: FrameInfo) -> Track:
        observed = self.last_frame == frame
        self.history.prune(frame.timestamp_s)
        return Track(
            self.identity,
            "observed" if observed else "lost",
            self.segment_id,
            self.history.observations,
            frame.timestamp_s - self.first_timestamp_s,
            frame.timestamp_s - self.last_frame.timestamp_s,
            self.observations_seen,
            self.consecutive_observations if observed else 0,
        )


class ByteTrackAdapter:
    """Associate by class and expose immutable measured tracks with explicit gaps."""

    def __init__(
        self, config: TrackingConfig | None = None, *, namespace: str | None = None
    ) -> None:
        try:
            import numpy as np
            import supervision as sv
            from trackers import ByteTrackTracker
        except ImportError as exc:
            raise RuntimeError("Tracking requires the optional tracking extra") from exc
        if namespace is not None and (not namespace or "/" in namespace):
            raise ValueError("Tracking namespace must be nonempty and contain no slash")
        self.config = config or TrackingConfig()
        self.namespace = namespace if namespace is not None else uuid4().hex
        self.epoch = 0
        self._np: Any = np
        self._sv: Any = sv
        self._backend: Any = ByteTrackTracker
        self._backends: dict[int, Any] = {}
        self._tracks: dict[tuple[int, int], _LiveTrack] = {}
        self._previous: FrameInfo | None = None

    def _reset(self, reason: TrackEndReason) -> tuple[TrackEnd, ...]:
        ended = tuple(TrackEnd(t.identity, reason) for t in self._tracks.values())
        self._backends.clear()
        self._tracks.clear()
        self._previous = None
        self.epoch += 1
        return ended

    def reset(self) -> tuple[TrackEnd, ...]:
        """End every track and advance the namespace epoch, even if already empty."""
        return self._reset("manual_reset")

    def _boundary(self, frame: FrameInfo) -> TrackEndReason | None:
        previous = self._previous
        if previous is None:
            return None
        if frame.source_id != previous.source_id:
            return "source_changed"
        if frame.index <= previous.index or frame.timestamp_s <= previous.timestamp_s:
            raise ValueError(
                "Frame indices and source timestamps must strictly increase"
            )
        if (frame.width, frame.height) != (previous.width, previous.height):
            return "resolution_changed"
        if frame.index != previous.index + 1:
            return "frame_gap"
        if frame.timestamp_s - previous.timestamp_s > self.config.max_gap_seconds:
            return "time_gap"
        return None

    def _associate(
        self, frame: FrameInfo, detections: Sequence[Detection]
    ) -> list[int | None]:
        np, sv, config = self._np, self._sv, self.config
        eligible = [i for i, d in enumerate(detections) if d.score >= config.low_score]
        for i in eligible:
            class_id = detections[i].class_id
            if class_id not in self._backends:
                self._backends[class_id] = self._backend(
                    frame_rate=config.frame_rate,
                    lost_track_buffer=config.lost_track_buffer,
                    minimum_consecutive_frames=2,
                    track_activation_threshold=config.activation_score,
                    high_conf_det_threshold=config.high_score,
                    minimum_iou_threshold=config.minimum_iou,
                )
        ids: list[int | None] = [None] * len(detections)
        for class_id, backend in self._backends.items():
            indices = [i for i in eligible if detections[i].class_id == class_id]
            inputs = sv.Detections(
                xyxy=np.array(
                    [detections[i].xyxy for i in indices], dtype=float
                ).reshape(-1, 4),
                confidence=np.array(
                    [detections[i].score for i in indices], dtype=float
                ),
                class_id=np.full(len(indices), class_id, dtype=int),
                data={"observation_index": np.array(indices, dtype=int)},
            )
            result = backend.update(inputs, timestamp=frame.timestamp_s)
            returned = result.data.get("observation_index", np.array([], dtype=int))
            if sorted(returned.tolist()) != indices:
                raise RuntimeError("Backend did not preserve observation indices")
            for j, index in enumerate(returned):
                detection = detections[int(index)]
                if (
                    not np.array_equal(result.xyxy[j], detection.xyxy)
                    or result.confidence[j] != detection.score
                    or result.class_id[j] != detection.class_id
                ):
                    raise RuntimeError("Backend changed an original measurement")
                identity = int(result.tracker_id[j])
                ids[int(index)] = identity if identity >= 0 else None
        return ids

    def update(
        self, frame: FrameInfo, detections: Sequence[Detection]
    ) -> TrackingResult:
        detections = tuple(detections)
        # Validate all external input before resetting or mutating backend state.
        if any(type(v) is not int for v in (frame.index, frame.width, frame.height)):
            raise ValueError("Tracking frame index and dimensions must be integers")
        if any(d.frame != frame for d in detections):
            raise ValueError("Detection refers to a different frame")
        if any(type(d.class_id) is not int for d in detections):
            raise ValueError("Detection class IDs must be integers")
        if any(not isinstance(d.xyxy, tuple) for d in detections):
            raise ValueError("Tracking requires immutable detection coordinates")
        reason = self._boundary(frame)
        ended = list(self._reset(reason)) if reason is not None else []
        try:
            ids = self._associate(frame, detections)
            confirmed = [
                (d.class_id, i)
                for d, i in zip(detections, ids, strict=True)
                if i is not None
            ]
            if len(set(confirmed)) != len(confirmed):
                raise RuntimeError("Backend assigned the same track twice in one frame")
        except Exception:
            # A partial multi-class update cannot safely be retried in its epoch.
            self._reset("backend_failure")
            raise
        observations = []
        for index, (detection, backend_id) in enumerate(
            zip(detections, ids, strict=True)
        ):
            live = None
            if backend_id is not None:
                key = (detection.class_id, backend_id)
                live = self._tracks.get(key)
                if live is None:
                    identity = TrackIdentity(
                        self.namespace, self.epoch, frame.source_id, *key
                    )
                    live = _LiveTrack(
                        identity,
                        ObservationHistory(self.config),
                        frame.timestamp_s,
                        frame,
                    )
                    self._tracks[key] = live
                live.observe(detection)
            observations.append(
                TrackedDetection(
                    index,
                    detection,
                    live.identity if live else None,
                    live.segment_id if live else None,
                    "below_floor"
                    if detection.score < self.config.low_score
                    else "associated"
                    if live
                    else "unassigned",
                )
            )
        snapshots = []
        for key, live in list(self._tracks.items()):
            if (
                frame.timestamp_s - live.last_frame.timestamp_s
                > self.config.effective_lost_seconds
            ):
                ended.append(TrackEnd(live.identity, "expired"))
                del self._tracks[key]
            else:
                snapshots.append(live.snapshot(frame))
        self._previous = frame
        return TrackingResult(
            frame, tuple(observations), tuple(snapshots), tuple(ended), reason
        )
