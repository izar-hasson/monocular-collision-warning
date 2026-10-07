"""Seed a NEW isolated venv from checksum-validated, locked baseline packages.

Recovery for unavailable upstream downloads. Follow with uv sync --locked to
reconcile the GPU closure. This verifies installed RECORDs, not upstream wheels;
record that distinction when reporting reproduction. Never alters the baseline.
"""

import argparse
import base64
import csv
import hashlib
import json
import shutil
import tomllib
from importlib.metadata import distributions
from pathlib import Path


def seed(baseline: Path, target: Path, lockfile: Path, report: Path) -> None:
    baseline, target = baseline.resolve(), target.resolve()
    if baseline == target or target.is_relative_to(baseline):
        raise ValueError("Target must be independent of the preserved baseline")
    source_site = baseline / "lib/python3.12/site-packages"
    target_site = target / "lib/python3.12/site-packages"
    if not source_site.is_dir() or not target_site.is_dir():
        raise ValueError("Both environments must already exist and use Python 3.12")
    if list(target_site.glob("*.dist-info")) or report.exists():
        raise ValueError("Use a fresh empty target environment and new report")
    lock = tomllib.loads(lockfile.read_text())
    versions: dict[str, set[str]] = {}
    for package in lock["package"]:
        versions.setdefault(package["name"], set()).add(package["version"])
    records = []
    for distribution in distributions(path=[str(source_site)]):
        name = distribution.metadata["Name"].lower().replace("_", "-")
        if distribution.version not in versions.get(name, set()):
            continue
        files = distribution.files
        if files is None:
            raise ValueError(f"Baseline distribution has no RECORD: {name}")
        copied = []
        for file in files:
            source = distribution.locate_file(file).resolve()
            destination = (target_site / str(file)).resolve()
            if not source.is_relative_to(baseline) or not destination.is_relative_to(
                target
            ):
                raise ValueError(f"Distribution path escapes environment: {file}")
            if not source.is_file():
                if file.hash is None:
                    continue
                raise ValueError(f"Baseline file missing: {file}")
            if file.hash is not None:
                with source.open("rb") as handle:
                    digest = hashlib.file_digest(handle, file.hash.mode).digest()
                encoded = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
                if encoded != file.hash.value:
                    raise ValueError(f"Baseline RECORD mismatch: {file}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            adapted = False
            if destination.parent == target / "bin":
                data = destination.read_bytes()
                if data.startswith(b"#!") and b"python" in data.split(b"\n", 1)[0]:
                    body = data.split(b"\n", 1)[1]
                    destination.write_bytes(
                        b"#!" + str(target / "bin/python").encode() + b"\n" + body
                    )
                    adapted = True
            copied.append({"path": str(file), "entrypoint_adapted": adapted})
        # Installers also rewrite entrypoint hashes for the new interpreter.
        record_file = next(f for f in files if str(f).endswith(".dist-info/RECORD"))
        record_path = target_site / str(record_file)
        rows = list(csv.reader(record_path.open()))
        for row in rows:
            path = (target_site / row[0]).resolve()
            if path.is_file() and row[1]:
                with path.open("rb") as handle:
                    digest = hashlib.file_digest(handle, "sha256").digest()
                row[1] = (
                    "sha256=" + base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
                )
                row[2] = str(path.stat().st_size)
        with record_path.open("w", newline="") as handle:
            csv.writer(handle).writerows(rows)
        records.append({"name": name, "version": distribution.version, "files": copied})
        print(f"Validated and seeded {name}=={distribution.version}", flush=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps({"packages": records, "baseline_modified": False}, indent=2) + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--lockfile", type=Path, default=Path("uv.lock"))
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    seed(args.baseline, args.target, args.lockfile, args.report)
