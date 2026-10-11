"""Fetch locked Linux/Python 3.12 cu130 wheels from the official alternate CDN.

Explicit recovery for download-r2 timeouts. Hashes come from uv.lock; no installed
baseline files are used. This command is never run by package imports or CPU CI.
"""

import argparse
import hashlib
import subprocess
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def download(url: str, expected: str, destination: Path) -> None:
    if destination.exists():
        if digest(destination) != expected:
            raise ValueError(f"Existing wheel hash mismatch: {destination.name}")
        return
    partial = destination.with_suffix(".whl.part")
    subprocess.run(
        [
            "curl",
            "--fail",
            "--location",
            "--retry",
            "2",
            "--connect-timeout",
            "20",
            "--max-time",
            "1800",
            "--continue-at",
            "-",
            "--output",
            str(partial),
            url,
        ],
        check=True,
    )
    if digest(partial) != expected:
        raise ValueError(f"Downloaded wheel hash mismatch: {destination.name}")
    partial.rename(destination)


def acquire(lockfile: Path, destination: Path) -> None:
    lock = tomllib.loads(lockfile.read_text())
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("torch", "torchvision"):
        packages = [
            p
            for p in lock["package"]
            if p["name"] == name
            and p["source"].get("registry") == "https://download.pytorch.org/whl/cu130"
        ]
        if len(packages) != 1:
            raise ValueError(f"Expected one locked cu130 package: {name}")
        package = packages[0]
        wheels = [
            w
            for w in package["wheels"]
            if urlsplit(w["url"]).path.endswith("cp312-cp312-manylinux_2_28_x86_64.whl")
        ]
        if len(wheels) != 1:
            raise ValueError(f"Expected one locked Linux/Python 3.12 wheel: {name}")
        wheel = wheels[0]
        source = urlsplit(wheel["url"])
        if (
            source.scheme != "https"
            or source.netloc not in {"download-r2.pytorch.org", "download.pytorch.org"}
            or not source.path.startswith("/whl/cu130/")
        ):
            raise ValueError("Wheel must come from the official cu130 index")
        algorithm, expected = wheel["hash"].split(":", 1)
        if algorithm != "sha256" or len(expected) != 64:
            raise ValueError("Locked wheel must have a SHA-256")
        filename = unquote(Path(source.path).name)
        alternate = urlunsplit(("https", "download.pytorch.org", source.path, "", ""))
        download(alternate, expected, destination / filename)
        print(f"Verified {filename}: {expected}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lockfile", type=Path, default=Path("uv.lock"))
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    acquire(args.lockfile, args.destination)
