"""Run three fixed full-CLI repetitions and independently validate their artifacts.

Requires the prepared KITTI clip/manifest and verified YOLO model/manifest.
All media and reports stay local. Visual review is a separate human/agent step.
"""

import argparse
import json
import math
import subprocess
from collections import Counter
from pathlib import Path

import av
import cv2

from collision_warning.detection import sha256_file


def verify(output: Path, clip: dict) -> dict:
    manifest = json.loads((output / "manifest.json").read_text())
    rows = [
        json.loads(line)
        for line in (output / "detections.jsonl").read_text().splitlines()
    ]
    expected = [pts / 1000 for pts in clip["expected_pts_ms"]]
    assert manifest["status"] == "complete"
    assert len(rows) == len(expected)
    assert [row["frame"]["timestamp_s"] for row in rows] == expected
    width, height = clip["video"]["width_px"], clip["video"]["height_px"]
    counts = Counter()
    for index, row in enumerate(rows):
        info = row["frame"]
        assert info == {
            "source_id": clip["id"],
            "index": index,
            "timestamp_s": expected[index],
            "width": width,
            "height": height,
        }
        assert row["color_space"] == "BGR"
        assert row["warmup"] == (index < 10)
        image = cv2.imread(str(output / row["annotated_image"]))
        assert image is not None and image.shape == (height, width, 3)
        for detection in row["detections"]:
            assert detection["frame"] == info
            assert detection["class_id"] in [0, 1, 2, 3, 5, 7]
            assert 0.1 <= detection["score"] <= 1
            x1, y1, x2, y2 = detection["xyxy"]
            assert all(math.isfinite(v) for v in (x1, y1, x2, y2))
            assert 0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height
            counts[detection["class_name"]] += 1
    assert len(list(output.glob("frame-*.jpg"))) == len(rows)
    with av.open(str(output / "detections.mp4")) as container:
        preview = list(container.decode(video=0))
    assert len(preview) == len(rows)
    assert all(
        (f.width, f.height) == (width + width % 2, height + height % 2) for f in preview
    )
    metrics = manifest["metrics"]
    assert metrics["frames_processed"] == len(rows)
    assert metrics["frames_dropped"] == 0
    assert metrics["class_counts"] == dict(counts)
    assert all(
        stage["count"] == len(rows) - 10 for stage in metrics["latency"].values()
    )
    source_fps = (len(rows) - 1) / (expected[-1] - expected[0])
    assert metrics["source_observed_rate_hz"] == source_fps
    return {
        "run": output.name,
        "metrics": metrics,
        "jsonl_sha256": sha256_file(output / "detections.jsonl"),
        "manifest_sha256": sha256_file(output / "manifest.json"),
        "preview_sha256": sha256_file(output / "detections.mp4"),
        "verified": (
            "All PTS, indices, dimensions, boxes, scores, warmth, counts, "
            "JPEGs and preview frames"
        ),
    }


def accept(
    executable: Path,
    source: Path,
    weights: Path,
    clip_path: Path,
    model_path: Path,
    output: Path,
) -> None:
    if output.exists():
        raise ValueError("Acceptance directory exists; preserve earlier evidence")
    output.mkdir(parents=True)
    clip = json.loads(clip_path.read_text())
    common = [
        str(executable.resolve()),
        "detect",
        "--source",
        str(source),
        "--weights",
        str(weights),
        "--clip-manifest",
        str(clip_path),
        "--model-manifest",
        str(model_path),
        "--device",
        "cuda:0",
        "--imgsz",
        "640",
        "--conf",
        "0.1",
        "--classes",
        "0",
        "1",
        "2",
        "3",
        "5",
        "7",
        "--warmup-frames",
        "10",
        "--max-frames",
        str(clip["video"]["frame_count"]),
        "--save-frames",
        "--save-video",
    ]
    report = {
        "schema_version": 1,
        "commands": [],
        "repetitions": [],
        "failure_checks": [],
    }

    def invoke(arguments: list[str], name: str) -> subprocess.CompletedProcess:
        result = subprocess.run(arguments, capture_output=True, text=True)
        (output / f"{name}.log").write_text(result.stdout + result.stderr)
        report["commands"].append({"argv": arguments, "exit_code": result.returncode})
        return result

    for repeat in range(1, 4):
        run = output / f"gpu-{repeat}"
        result = invoke([*common, "--output", str(run)], run.name)
        if result.returncode:
            raise RuntimeError(f"CLI failed; inspect {output / (run.name + '.log')}")
        report["repetitions"].append(verify(run, clip))
    signatures = [r["jsonl_sha256"] for r in report["repetitions"]]
    report["identical_jsonl_across_repeats"] = len(set(signatures)) == 1

    # Preflight rejection must preserve completed evidence and create no new run.
    reuse = output / "gpu-1"
    before = sha256_file(reuse / "manifest.json")
    result = invoke([*common, "--output", str(reuse)], "existing-output")
    assert result.returncode == 1 and "already exists" in result.stderr
    assert sha256_file(reuse / "manifest.json") == before
    report["failure_checks"].append("Existing output rejected without modification")

    bad_model = output / "bad-model.json"
    model = json.loads(model_path.read_text())
    model["sha256"] = "0" * 64
    bad_model.write_text(json.dumps(model))
    args = common.copy()
    args[args.index("--model-manifest") + 1] = str(bad_model)
    rejected = output / "checksum-mismatch"
    result = invoke([*args, "--output", str(rejected)], "checksum-mismatch")
    assert result.returncode == 1 and "SHA-256 mismatch" in result.stderr
    assert not rejected.exists()
    report["failure_checks"].append("Model checksum mismatch rejected before output")

    args = common.copy()
    args[args.index("--source") + 1] = str(output / "missing.mkv")
    rejected = output / "missing-source"
    result = invoke([*args, "--output", str(rejected)], "missing-source")
    assert result.returncode == 1 and not rejected.exists()
    report["failure_checks"].append("Missing source rejected before output")

    args = common.copy()
    args[args.index("--device") + 1] = "cuda:999"
    rejected = output / "invalid-device"
    result = invoke([*args, "--output", str(rejected)], "invalid-device")
    assert result.returncode == 1 and "device index does not exist" in result.stderr
    failed = json.loads((rejected / "manifest.json").read_text())
    assert failed["status"] == "failed" and failed["metrics"] is None
    report["failure_checks"].append("Invalid CUDA device leaves failed manifest")

    corrupt = output / "corrupt.mkv"
    corrupt.write_bytes(b"deliberately invalid video")
    card = {**clip, "sha256": sha256_file(corrupt)}
    corrupt_card = output / "corrupt.json"
    corrupt_card.write_text(json.dumps(card))
    args = common.copy()
    args[args.index("--source") + 1] = str(corrupt)
    args[args.index("--clip-manifest") + 1] = str(corrupt_card)
    rejected = output / "corrupt-video"
    result = invoke([*args, "--output", str(rejected)], "corrupt-video")
    assert result.returncode == 1
    failed = json.loads((rejected / "manifest.json").read_text())
    assert failed["status"] == "failed" and failed["failure"]
    report["failure_checks"].append("Invalid video leaves failed manifest")
    report["visual_review"] = "pending; inspect representative annotated frames"
    (output / "acceptance.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--executable", type=Path, default=Path(".venv-gpu/bin/collision-warning")
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--clip-manifest", type=Path, required=True)
    parser.add_argument("--model-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    accept(
        args.executable,
        args.source,
        args.weights,
        args.clip_manifest,
        args.model_manifest,
        args.output,
    )
