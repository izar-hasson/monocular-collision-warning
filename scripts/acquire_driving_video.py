"""Acquire comma.ai's published dashcam sample for a local detection smoke test."""

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

SOURCE = (
    "https://media.githubusercontent.com/media/commaai/"
    "comma_video_compression_challenge/master/videos/0.mkv"
)
SHA256 = "2611f5f3e186f3529777749f97bd4cce3a208d6b3559e137bd45d256980d2fa9"
SIZE = 37545489
REPOSITORY = "https://github.com/commaai/comma_video_compression_challenge"


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def acquire(destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.stat().st_size != SIZE or sha256(destination) != SHA256:
            raise ValueError("Existing video differs from the upstream sample")
    else:
        partial = destination.with_suffix(destination.suffix + ".part")
        subprocess.run(
            [
                "curl",
                "--fail",
                "--location",
                "--retry",
                "2",
                "--connect-timeout",
                "15",
                "--max-time",
                "240",
                "--continue-at",
                "-",
                "--output",
                str(partial),
                SOURCE,
            ],
            check=True,
        )
        if partial.stat().st_size != SIZE or sha256(partial) != SHA256:
            raise ValueError(
                "Downloaded video does not match the upstream LFS checksum"
            )
        partial.rename(destination)
    manifest = {
        "schema_version": 1,
        "id": "comma-video-compression-challenge-0",
        "source_url": SOURCE,
        "publisher_page": REPOSITORY,
        "upstream_pointer_url": (
            "https://raw.githubusercontent.com/commaai/"
            "comma_video_compression_challenge/master/videos/0.mkv"
        ),
        "sha256": SHA256,
        "size_bytes": SIZE,
        "acquired_at_utc": datetime.now(UTC).isoformat(),
        "license": "Publisher repository MIT licence; Copyright (c) 2026 comma.ai",
        "license_url": REPOSITORY + "/blob/master/LICENSE",
        "permitted_use": "Local experimentation with the publisher's challenge sample",
        "redistribution": "No raw or annotated media published by this acquisition",
        "split": "development",
        "reference_labels": None,
        "privacy": "Road users/plates may be visible; keep media local",
        "limitations": [
            "Single development clip; no accuracy or risk-reference labels"
        ],
    }
    destination.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Verified driving video: {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path("data/external/comma-video/0.mkv"),
    )
    acquire(parser.parse_args().destination)
