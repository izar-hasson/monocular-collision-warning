"""Local video decoding with source presentation timestamps, never wall time."""

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any

from collision_warning.domain import Frame, FrameInfo


def video_properties(path: Path) -> dict[str, float]:
    """Preview metadata from the first video stream used by read_video."""
    try:
        import av
    except ImportError as exc:
        raise RuntimeError(
            "Video input requires PyAV; install the video extra"
        ) from exc
    with av.open(str(path)) as container:
        if not container.streams.video:
            raise ValueError("Input contains no video stream")
        stream = container.streams.video[0]
        return {
            "nominal_fps": float(stream.average_rate) if stream.average_rate else 0.0,
            "reported_frames": float(stream.frames),
        }


def decoded_frames(decoded: Any, source_id: str) -> Iterator[Frame]:
    """Translate PyAV frames; this boundary also permits synthetic CPU inputs."""
    previous: float | None = None
    for index, raw in enumerate(decoded):
        if raw.pts is None or raw.time_base is None or raw.time_base <= 0:
            raise ValueError(f"Frame {index} has no usable presentation timestamp")
        timestamp = float(raw.pts * raw.time_base)
        info = FrameInfo(source_id, index, timestamp, raw.width, raw.height)
        if previous is not None and timestamp <= previous:
            raise ValueError(f"Frame {index} presentation timestamp did not increase")
        previous = timestamp
        yield Frame(info, raw.to_ndarray(format="bgr24"))


def read_video(path: Path, source_id: str) -> Generator[Frame, None, None]:
    """Decode the first video stream; the container closes even on early exit."""
    if not path.is_file():
        raise ValueError(f"Video does not exist: {path}")
    try:
        import av
    except ImportError as exc:
        raise RuntimeError(
            "PyAV is not installed; install the video extra (uv sync --extra video)"
        ) from exc
    with av.open(str(path)) as container:
        if not container.streams.video:
            raise ValueError("Input contains no video stream")
        yield from decoded_frames(container.decode(video=0), source_id)
