"""Shared detection-run orchestration for the CLI and checkout test script."""

import json
import platform
import subprocess
from contextlib import ExitStack
from dataclasses import asdict
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from math import isfinite
from pathlib import Path
from time import perf_counter
from typing import Any

from collision_warning.detection import (
    DetectorConfig,
    YoloDetector,
    sha256_file,
    verify_asset,
)
from collision_warning.inputs import image_frames, is_image_source
from collision_warning.pipeline import run_detection
from collision_warning.preview import AnnotatedPreview
from collision_warning.video import read_video, video_properties


def read_asset_manifest(path: Path, kind: str) -> dict[str, Any]:
    """Require provenance at the input boundary, without inventing missing rights."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError(f"{kind} manifest must be a version-1 JSON object")
    required = ("id", "sha256", "source_url", "license", "permitted_use")
    if any(not isinstance(value.get(k), str) or not value[k].strip() for k in required):
        raise ValueError(f"{kind} manifest requires: {', '.join(required)}")
    if kind == "clip" and value.get("split") not in {"development", "held-out"}:
        raise ValueError("Clip manifest must declare development or held-out split")
    return value


def environment_metadata(device: str) -> dict[str, Any]:
    packages: dict[str, str | None] = {}
    for name in (
        "monocular-collision-warning",
        "av",
        "numpy",
        "torch",
        "torchvision",
        "ultralytics",
        "opencv-python",
    ):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    metadata: dict[str, Any] = {
        "python": platform.python_version(),
        "os": platform.system(),
        "machine": platform.machine(),
        "device": device,
        "precision": "float32",
        "package_versions": packages,
        "hardware": platform.processor() or None,
        "driver": None,
    }
    if device.startswith("cuda:"):
        import torch

        metadata["hardware"] = torch.cuda.get_device_name(device)
        metadata["cuda_build"] = torch.version.cuda
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            metadata["driver"] = result.stdout.strip().splitlines()[int(device[5:])]
        except (OSError, subprocess.SubprocessError, IndexError):
            pass
    return metadata


def code_metadata() -> dict[str, Any]:
    """Record checkout identity when running from a repo; absent for a wheel."""
    root = Path(__file__).resolve().parents[2]
    if not (root / "pyproject.toml").is_file():
        return {"commit": None, "dirty": None, "lockfile_sha256": None}
    result: dict[str, Any] = {"commit": None, "dirty": None}
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        result.update(commit=commit.stdout.strip(), dirty=bool(status.stdout.strip()))
    except (OSError, subprocess.SubprocessError):
        pass
    lock = root / "uv.lock"
    result["lockfile_sha256"] = sha256_file(lock) if lock.is_file() else None
    return result


def detect_source(
    source: Path,
    weights: Path,
    clip_manifest: Path | None,
    model_manifest: Path | None,
    output: Path,
    config: DetectorConfig,
    *,
    warmup_frames: int,
    max_frames: int | None,
    expected_sha256: str | None = None,
    save_frames: bool = False,
    save_video: bool = False,
) -> dict[str, Any]:
    """Use one pipeline; supplied provenance is verified, absent provenance recorded."""
    if not source.exists():
        raise ValueError("Source does not exist")
    if not weights.is_file():
        raise ValueError("Weights must be an existing local .pt file")
    if warmup_frames < 0 or (max_frames is not None and max_frames <= 0):
        raise ValueError("Warm-up must be nonnegative and frame limit positive")
    is_images = is_image_source(source)
    if save_video and is_images:
        raise ValueError(
            "Saving a preview video requires video input with a nominal FPS"
        )
    acquisition = source / "acquisition.json"
    clip: dict[str, Any] = (
        read_asset_manifest(clip_manifest, "clip")
        if clip_manifest is not None
        else {
            "id": source.name,
            "sha256": sha256_file(source) if source.is_file() else None,
            "provenance": "not supplied",
            "acquisition_manifest_sha256": (
                sha256_file(acquisition)
                if source.is_dir() and acquisition.is_file()
                else None
            ),
        }
    )
    model: dict[str, Any] = (
        read_asset_manifest(model_manifest, "model")
        if model_manifest is not None
        else {
            "id": weights.name,
            "sha256": expected_sha256 or sha256_file(weights),
            "provenance": "not supplied",
        }
    )
    if clip_manifest is not None:
        verify_asset(source, clip["sha256"])
    verify_asset(weights, model["sha256"])
    if expected_sha256 is not None:
        verify_asset(weights, expected_sha256)
    if output.exists():
        raise ValueError("Output directory already exists; choose a new run directory")
    output.mkdir(parents=True)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "status": "running",
        "started_at_utc": datetime.now(UTC).isoformat(),
        "input": clip,
        "code": code_metadata(),
        "model": model,
        "configuration": {
            **asdict(config),
            "warmup_frames": warmup_frames,
            "max_frames": max_frames,
        },
        "environment": None,
        "protocol": {
            "batch_size": 1,
            "timestamp_convention": (
                "KITTI relative source timestamps"
                if source.is_dir()
                else "still image; timestamp zero is a placeholder"
                if is_images
                else "source presentation timestamp, pts * time_base"
            ),
            "timing_method": "perf_counter; CUDA synchronized around inference",
            "included_stages": ["decode", "detect", "JSONL output"],
            "repeat_count": 1,
        },
        "metrics": None,
        "failure": None,
        "video": None,
        "artifacts": ["detections.jsonl"],
        "limitations": [
            "Development demonstration; no reference-box accuracy evaluation.",
            "No TTC, metric range, path overlap or collision warnings.",
            "End-to-end timing excludes model loading and input checksum validation.",
            "Frame timing excludes preview finalization and final manifest writing.",
            "Source rate is measured over processed PTS, not container nominal FPS.",
        ],
    }
    frames = (
        image_frames(source, clip["id"])
        if is_images
        else read_video(source, clip["id"])
    )
    preview = None
    try:
        with ExitStack() as stack:
            stack.callback(frames.close)
            fps = None
            if save_video:
                manifest["video"] = video_properties(source)
                fps = manifest["video"]["nominal_fps"]
                if not isfinite(fps) or fps <= 0:
                    raise ValueError("Saving a preview video requires a nominal FPS")
                manifest["limitations"].append(
                    "Preview uses nominal FPS; JSONL retains source frame times."
                )
            if save_frames or save_video:
                preview = AnnotatedPreview(output, save_frames=save_frames, fps=fps)
                stack.callback(preview.close)
                manifest["protocol"]["output_includes_preview"] = True
                if save_frames:
                    manifest["artifacts"].append("frame-*.jpg")
            load_start = perf_counter()
            detector = YoloDetector(weights, model["sha256"], config)
            detector.synchronize()
            manifest["model_load_s"] = perf_counter() - load_start
            manifest["environment"] = environment_metadata(config.device)
            manifest["metrics"] = run_detection(
                frames,
                detector,
                output / "detections.jsonl",
                warmup_frames=warmup_frames,
                max_frames=max_frames,
                preview=preview,
            )
        manifest["status"] = "complete"
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        if preview is not None:
            manifest["artifacts"].extend(preview.artifacts)
        (output / "manifest.json").write_text(
            json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
    return manifest


# Keep the original video-only entry point compatible with existing callers.
detect_video = detect_source
