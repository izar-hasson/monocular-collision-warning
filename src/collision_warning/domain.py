"""Dependency-free observations shared by the video and perception adapters."""

from dataclasses import dataclass
from math import isfinite
from typing import Literal


@dataclass(frozen=True)
class FrameInfo:
    source_id: str
    index: int
    timestamp_s: float
    width: int
    height: int

    def __post_init__(self) -> None:
        if not self.source_id or self.index < 0:
            raise ValueError("Frame requires a source ID and nonnegative index")
        if not isfinite(self.timestamp_s):
            raise ValueError("Source timestamp must be finite")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Frame dimensions must be positive")


@dataclass(frozen=True)
class Frame:
    info: FrameInfo
    image: object  # HWC uint8 BGR; owned by the decoder, never retained in history.


@dataclass(frozen=True)
class Detection:
    frame: FrameInfo
    class_id: int
    class_name: str
    score: float
    xyxy: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        if self.class_id < 0 or not self.class_name:
            raise ValueError("Detection requires a nonnegative class and name")
        if not isfinite(self.score) or not 0 <= self.score <= 1:
            raise ValueError("Detection score must be finite and in [0, 1]")
        if len(self.xyxy) != 4 or not all(isfinite(v) for v in self.xyxy):
            raise ValueError("Box must contain four finite pixel coordinates")
        x1, y1, x2, y2 = self.xyxy
        if not (0 <= x1 < x2 <= self.frame.width):
            raise ValueError("Box x coordinates must be ordered and inside the frame")
        if not (0 <= y1 < y2 <= self.frame.height):
            raise ValueError("Box y coordinates must be ordered and inside the frame")


@dataclass(frozen=True)
class TrackIdentity:
    namespace: str
    epoch: int
    source_id: str
    class_id: int
    backend_id: int

    @property
    def value(self) -> str:
        return f"{self.namespace}/{self.epoch}/{self.class_id}/{self.backend_id}"


@dataclass(frozen=True)
class TrackedDetection:
    observation_index: int
    detection: Detection
    identity: TrackIdentity | None
    segment_id: int | None
    status: Literal["associated", "unassigned", "below_floor"]


@dataclass(frozen=True)
class Track:
    """Immutable snapshot; history contains measurements in this segment only."""

    identity: TrackIdentity
    state: Literal["observed", "lost"]
    segment_id: int
    history: tuple[Detection, ...]
    age_s: float
    time_since_observed_s: float
    observations_seen: int
    consecutive_observations: int


TrackEndReason = Literal[
    "expired",
    "manual_reset",
    "source_changed",
    "resolution_changed",
    "frame_gap",
    "time_gap",
    "backend_failure",
]


@dataclass(frozen=True)
class TrackEnd:
    identity: TrackIdentity
    reason: TrackEndReason


@dataclass(frozen=True)
class TrackingResult:
    frame: FrameInfo
    observations: tuple[TrackedDetection, ...]
    tracks: tuple[Track, ...]
    ended_tracks: tuple[TrackEnd, ...]
    reset_reason: TrackEndReason | None
