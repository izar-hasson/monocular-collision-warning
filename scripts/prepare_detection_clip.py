"""Encode acquired KITTI frames losslessly and verify pixels and source times.

Run with the locked GPU environment from the repository root. Media and completed
manifests stay local. This creates video from an image sequence, not native video.
"""

import argparse
import json
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path

import av
import cv2
import numpy as np

from collision_warning.detection import sha256_file
from collision_warning.inputs import sequence_times


def prepare(source: Path, output: Path, frames: int) -> None:
    if output.exists() or output.with_suffix(".json").exists():
        raise ValueError("Clip or manifest exists; choose a new output")
    acquisition = json.loads((source / "acquisition.json").read_text())
    records = acquisition["frames"][:frames]
    if len(records) != frames or not 100 <= frames <= 300:
        raise ValueError("Acceptance requires 100–300 acquired consecutive frames")
    times = sequence_times(source / "timestamps.txt")[:frames]
    expected_pts = [round((5 + time) * 1000) for time in times]
    images = []
    for index, record in enumerate(records):
        path = source / record["local_name"]
        if int(path.stem) != index or sha256_file(path) != record["sha256"]:
            raise ValueError("Source frame order or checksum changed")
        images.append(path)
    first = cv2.imread(str(images[0]))
    height, width = first.shape[:2]
    output.parent.mkdir(parents=True, exist_ok=True)
    with av.open(str(output), "w") as container:
        stream = container.add_stream("ffv1", rate=Fraction(10))
        stream.width, stream.height = width, height
        stream.pix_fmt = "bgr0"
        stream.time_base = Fraction(1, 1000)
        stream.codec_context.time_base = Fraction(1, 1000)
        for path, pts in zip(images, expected_pts, strict=True):
            image = cv2.imread(str(path))
            if image is None or image.shape != first.shape:
                raise ValueError("Source image missing or dimensions changed")
            frame = av.VideoFrame.from_ndarray(image, format="bgr24")
            frame.pts, frame.time_base = pts, Fraction(1, 1000)
            container.mux(stream.encode(frame))
        container.mux(stream.encode())
    with av.open(str(output)) as container:
        decoded = list(container.decode(video=0))
    if len(decoded) != frames:
        raise ValueError("Encoded frame count changed")
    for path, raw, pts in zip(images, decoded, expected_pts, strict=True):
        if raw.pts * raw.time_base != Fraction(pts, 1000):
            raise ValueError("Encoded timestamp changed")
        if not np.array_equal(cv2.imread(str(path)), raw.to_ndarray(format="bgr24")):
            raise ValueError("Lossless pixel verification failed")
    manifest = {
        "schema_version": 1,
        "id": f"kitti-0005-image02-first-{frames}-ffv1",
        "sha256": sha256_file(output),
        "source_url": acquisition["source_url"],
        "license": acquisition["license"],
        "license_url": acquisition["license_url"],
        "permitted_use": acquisition["permitted_use"],
        "attribution": acquisition["attribution"],
        "split": "development",
        "sequence": acquisition["sequence"],
        "camera": acquisition["camera"],
        "frame_range_inclusive": [0, frames - 1],
        "acquired_at_utc": acquisition["acquired_at_utc"],
        "prepared_at_utc": datetime.now(UTC).isoformat(),
        "acquisition_manifest_sha256": sha256_file(source / "acquisition.json"),
        "timestamps_sha256": acquisition["timestamps_sha256"],
        "source_timestamp_strings": (source / "timestamps.txt")
        .read_text()
        .splitlines()[:frames],
        "source_relative_times_s": times,
        "expected_pts_ms": expected_pts,
        "video": {
            "width_px": width,
            "height_px": height,
            "frame_count": frames,
            "codec": "FFV1",
            "container": "Matroska",
            "pixel_format": "bgr0; decoded bgr24",
            "nominal_fps": 10,
            "time_base": "1/1000",
            "timestamp_transform": (
                "relative KITTI image_02 acquisition times + 5 seconds, "
                "rounded to nearest millisecond"
            ),
            "maximum_timestamp_rounding_error_s": max(
                abs(pts / 1000 - (5 + time))
                for pts, time in zip(expected_pts, times, strict=True)
            ),
            "pixel_verification": (
                "Every decoded BGR frame equals its source PNG exactly"
            ),
            "encoding_changes": (
                "PNG sequence to lossless FFV1; no resize, crop, dropped or "
                "duplicated frames; nominal 10 FPS metadata, irregular source "
                "intervals preserved to milliseconds"
            ),
        },
        "encoding_environment": {
            "av": av.__version__,
            "numpy": np.__version__,
            "opencv": cv2.__version__,
            "ffmpeg_libraries": av.library_versions,
        },
        "reference": {
            "label_types": [],
            "status": "No reference boxes acquired; accuracy evaluation deferred",
        },
        "calibration": None,
        "privacy_review": (
            "Faces/plates may be visible; raw and annotated media remain local"
        ),
        "sequence_split_review": (
            "Entire drive_0005 belongs to development; never use other excerpts "
            "of this drive as held-out data"
        ),
        "limitations": [
            "Locally encoded image sequence, not native recorded video",
            "One short development sequence; no accuracy/generalization claim",
            "Source dates have no declared timezone; only relative time is used",
        ],
    }
    output.with_suffix(".json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Verified {frames} lossless frames and PTS: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=150)
    args = parser.parse_args()
    prepare(args.source, args.output, args.frames)
