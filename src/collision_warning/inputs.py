"""Still-image and KITTI inputs using the same frame contract as video."""

from collections.abc import Generator
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from collision_warning.domain import Frame, FrameInfo


def is_image_source(source: Path) -> bool:
    return source.is_dir() or source.suffix.lower() in {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp",
        ".tif",
        ".tiff",
    }


def sequence_times(path: Path) -> list[float]:
    """KITTI timestamp differences, retaining nanoseconds without assuming a zone."""
    values = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        whole, fraction = text.split(".", 1)
        date = datetime.strptime(whole, "%Y-%m-%d %H:%M:%S")
        if not fraction.isdigit() or len(fraction) > 9:
            raise ValueError("Invalid KITTI timestamp fractional seconds")
        values.append((date, Decimal("0." + fraction)))
    if not values:
        raise ValueError("Timestamp file is empty")
    origin, subsecond = values[0]
    times = [
        float(Decimal(int((date - origin).total_seconds())) + part - subsecond)
        for date, part in values
    ]
    if any(after <= before for before, after in zip(times, times[1:], strict=False)):
        raise ValueError("Sequence timestamps must increase")
    return times


def image_frames(source: Path, source_id: str) -> Generator[Frame, None, None]:
    """Load a still image or KITTI sequence, preserving acquisition time."""
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("Image input requires OpenCV installed") from exc
    if source.is_dir():
        timestamps = sequence_times(source / "timestamps.txt")
        images = sorted(source.glob("*.png"))
        if not images:
            raise ValueError("Sequence directory contains no PNG frames")
    else:
        timestamps = [0.0]  # A still image has no temporal measurement.
        images = [source]
    for path in images:
        index = int(path.stem) if source.is_dir() else 0
        if not 0 <= index < len(timestamps):
            raise ValueError("Image index has no matching source timestamp")
        pixels = cv2.imread(str(path))
        if pixels is None:
            raise ValueError(f"Could not read image: {path.name}")
        height, width = pixels.shape[:2]
        yield Frame(
            FrameInfo(source_id, index, timestamps[index], width, height), pixels
        )
