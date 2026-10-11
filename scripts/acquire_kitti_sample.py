"""Fetch a bounded monocular KITTI sample from its official public AWS mirror.

Media remains local. Verify ZIP member CRCs and record per-file SHA-256 and terms.
This does not acquire reference labels or establish an evaluation dataset.
"""

import argparse
import hashlib
import io
import json
import struct
import time
import urllib.request
import zipfile
import zlib
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

URL = (
    "https://avg-kitti.s3.eu-central-1.amazonaws.com/raw_data/"
    "2011_09_26_drive_0005/2011_09_26_drive_0005_sync.zip"
)
SIZE = 645940900
ETAG = '"6a880679a3e3eda8a0ef83abc5354eb1-78"'
CHUNK = 256 * 1024


def fetch_range(start: int, count: int) -> bytes:
    end = start + count - 1
    request = urllib.request.Request(
        URL, headers={"Range": f"bytes={start}-{end}", "If-Match": ETAG}
    )
    for attempt in range(8):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                expected = f"bytes {start}-{end}/{SIZE}"
                if (
                    response.status != 206
                    or response.headers.get("Content-Range") != expected
                ):
                    raise ValueError("Archive server did not honor the bounded request")
                data = response.read(count)
            if len(data) != count:
                raise OSError("Archive range response was truncated")
            return data
        except (OSError, TimeoutError):
            if attempt == 7:
                raise
            time.sleep(min(2**attempt, 10))
    raise RuntimeError("Archive request failed")


class RemoteArchive(io.RawIOBase):
    def __init__(self) -> None:
        self.position = 0

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = 0) -> int:
        origins = {0: 0, 1: self.position, 2: SIZE}
        self.position = origins[whence] + offset
        return self.position

    def read(self, size: int = -1) -> bytes:
        count = SIZE - self.position if size < 0 else min(size, SIZE - self.position)
        if count <= 0:
            return b""
        chunks = []
        while count:
            amount = min(CHUNK, count)
            chunks.append(fetch_range(self.position, amount))
            self.position += amount
            count -= amount
        return b"".join(chunks)


def acquire(
    destination: Path, frame_count: int, archive_path: Path | None = None
) -> None:
    if not 1 <= frame_count <= 300:
        raise ValueError("Choose 1–300 frames for this bounded development sample")
    destination.mkdir(parents=True, exist_ok=True)
    parts = destination / ".download-parts"
    parts.mkdir(exist_ok=True)
    if archive_path is not None and archive_path.stat().st_size != SIZE:
        raise ValueError("Local archive size differs from the selected upstream object")
    with zipfile.ZipFile(archive_path or RemoteArchive()) as archive:
        names = archive.namelist()
        selected = sorted(
            n for n in names if "/image_02/data/" in n and n.endswith(".png")
        )[:frame_count]
        if len(selected) != frame_count:
            raise ValueError("Sequence contains fewer frames than requested")
        timestamp_name = next(
            n for n in names if n.endswith("/image_02/timestamps.txt")
        )
        (destination / "timestamps.txt").write_bytes(archive.read(timestamp_name))
        infos = [archive.getinfo(name) for name in selected]
        if archive_path is not None:
            for info in infos:
                # ZipFile.read checks each member's CRC before returning it.
                (destination / Path(info.filename).name).write_bytes(archive.read(info))

    requests = []
    ranges = {}
    for info in infos:
        output = destination / Path(info.filename).name
        if output.exists() and output.stat().st_size == info.file_size:
            if zlib.crc32(output.read_bytes()) == info.CRC:
                continue
        length = 30 + len(info.filename.encode()) + 1024 + info.compress_size
        ranges[info.filename] = []
        for offset in range(0, length, CHUNK):
            position = info.header_offset + offset
            count = min(CHUNK, length - offset, SIZE - position)
            part = parts / f"{position}-{count}"
            ranges[info.filename].append(part)
            requests.append((position, count, part))

    def fetch(request: tuple[int, int, Path]) -> None:
        position, count, part = request
        if not part.exists() or part.stat().st_size != count:
            part.write_bytes(fetch_range(position, count))

    with ThreadPoolExecutor(max_workers=32) as pool:
        for completed, _ in enumerate(pool.map(fetch, requests), 1):
            if completed % 20 == 0:
                print(f"Fetched {completed}/{len(requests)} ranges", flush=True)

    records = []
    for info in infos:
        output = destination / Path(info.filename).name
        if info.filename in ranges:
            data = b"".join(part.read_bytes() for part in ranges[info.filename])
            if data[:4] != b"PK\x03\x04":
                raise ValueError("Invalid ZIP local header")
            name_length, extra_length = struct.unpack_from("<HH", data, 26)
            offset = 30 + name_length + extra_length
            compressed = data[offset : offset + info.compress_size]
            if info.compress_type == zipfile.ZIP_DEFLATED:
                pixels = zlib.decompress(compressed, -15)
            elif info.compress_type == zipfile.ZIP_STORED:
                pixels = compressed
            else:
                raise ValueError("Unsupported ZIP member compression")
            if len(pixels) != info.file_size or zlib.crc32(pixels) != info.CRC:
                raise ValueError("ZIP member integrity failed")
            output.write_bytes(pixels)
        records.append(
            {
                "member": info.filename,
                "local_name": output.name,
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "zip_crc32": info.CRC,
                "size_bytes": info.file_size,
            }
        )
    manifest = {
        "schema_version": 1,
        "dataset": "KITTI raw",
        "sequence": "2011_09_26_drive_0005",
        "camera": "image_02",
        "source_url": URL,
        "archive_size_bytes": SIZE,
        "archive_etag": ETAG,
        "archive_sha256": (
            hashlib.file_digest(archive_path.open("rb"), "sha256").hexdigest()
            if archive_path is not None
            else None
        ),
        "acquired_at_utc": datetime.now(UTC).isoformat(),
        "split": "development",
        "license": "CC-BY-NC-SA-3.0",
        "license_url": "https://www.cvlibs.net/datasets/kitti/",
        "registry_url": "https://registry.opendata.aws/kitti/",
        "attribution": (
            "Andreas Geiger, Philip Lenz, Christoph Stiller, Raquel Urtasun; "
            "Vision meets Robotics: The KITTI Dataset (2013)"
        ),
        "permitted_use": "Local noncommercial research demonstration",
        "redistribution": "No media published by this acquisition",
        "timestamps_member": timestamp_name,
        "timestamps_sha256": hashlib.sha256(
            (destination / "timestamps.txt").read_bytes()
        ).hexdigest(),
        "frames": records,
        "limitations": [
            "Small development excerpt; no reference labels acquired",
            "Faces/plates may be visible; keep media local",
        ],
    }
    (destination / "acquisition.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Verified {len(records)} RGB frames: {destination}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=12)
    parser.add_argument("--archive", type=Path, help="Already downloaded official ZIP")
    args = parser.parse_args()
    acquire(args.destination, args.frames, args.archive)
