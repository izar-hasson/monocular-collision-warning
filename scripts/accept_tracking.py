"""Run matched installed-CLI detection/tracking repetitions on declared local media.

Run with the GPU environment's Python; assets/rights are supplied, never acquired.
The report is local evidence, not ground-truth identity or warning evaluation.
"""

import argparse
import hashlib
import json
import statistics
import subprocess
import sysconfig
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter


def digest(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def load_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def measurements(rows):
    return [{"frame": r["frame"], "detections": r["detections"]} for r in rows]


def verify_tracking(original, tracked, config):
    assert len(original) == len(tracked)
    groups = defaultdict(list)
    counts = Counter()
    ended = Counter()
    max_history = max_retained = max_live = 0
    for raw, row in zip(original, tracked, strict=True):
        assert row["frame"] == raw["frame"]
        assert [o["detection"] for o in row["observations"]] == raw["detections"]
        assert [o["observation_index"] for o in row["observations"]] == list(
            range(len(raw["detections"]))
        )
        snapshots = {t["track_id"]: t for t in row["tracks"]}
        for observation in row["observations"]:
            counts[observation["status"]] += 1
            if observation["track_id"] is not None:
                live = snapshots[observation["track_id"]]
                assert live["state"] == "observed"
                assert live["segment_id"] == observation["segment_id"]
                groups[
                    (
                        observation["track_id"],
                        observation["segment_id"],
                        observation["detection"]["class_id"],
                    )
                ].append(raw["frame"]["index"])
                if observation["detection"]["score"] < config["high_score"]:
                    counts["low_score_associated"] += 1
        for track in row["tracks"]:
            assert 0 <= track["history_size"] <= config["history_max_observations"]
            if track["history_size"]:
                assert (
                    row["frame"]["timestamp_s"] - track["history_first_timestamp_s"]
                    <= config["history_max_seconds"] + 1e-9
                )
                assert track["history_last_timestamp_s"] <= row["frame"]["timestamp_s"]
                if track["state"] == "lost":
                    assert (
                        track["history_last_timestamp_s"] < row["frame"]["timestamp_s"]
                    )
        ended.update(t["reason"] for t in row["ended_tracks"])
        max_history = max(
            max_history, max((t["history_size"] for t in row["tracks"]), default=0)
        )
        max_retained = max(max_retained, sum(t["history_size"] for t in row["tracks"]))
        max_live = max(max_live, len(row["tracks"]))
    for indices in groups.values():
        assert all(b == a + 1 for a, b in zip(indices, indices[1:], strict=False))
    examples = []
    for category in sorted({key[2] for key in groups}):
        key = max((k for k in groups if k[2] == category), key=lambda k: len(groups[k]))
        indices = groups[key]
        examples.append(
            {
                "track_id": key[0],
                "segment_id": key[1],
                "class_id": category,
                "consecutive_observations": len(indices),
                "review_frames": [indices[0], indices[len(indices) // 2], indices[-1]],
            }
        )
    reentries = []
    for key, indices in groups.items():
        previous = (key[0], key[1] - 1, key[2])
        if previous in groups:
            reentries.append(
                {
                    "track_id": key[0],
                    "class_id": key[2],
                    "segments": [key[1] - 1, key[1]],
                    "review_frames": [groups[previous][-1], indices[0]],
                }
            )
    return {
        "counts": dict(counts),
        "ended": dict(ended),
        "continuity_segments": len(groups),
        "peak_history_per_track": max_history,
        "peak_retained_observations": max_retained,
        "peak_live_tracks": max_live,
        "continuous_examples": examples,
        "reacquisition_examples": reentries[:5],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in [
        "source",
        "weights",
        "clip-manifest",
        "model-manifest",
        "reference-detections",
        "output",
    ]:
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmup-frames", type=int, default=10)
    parser.add_argument("--max-frames", type=int, default=100)
    args = parser.parse_args()
    if args.repeats <= 0 or not 0 <= args.warmup_frames < args.max_frames:
        parser.error("Require positive repetitions and 0 <= warmup < max frames")
    args.output.mkdir(parents=True, exist_ok=False)
    executable = Path(sysconfig.get_path("scripts")) / "collision-warning"
    common = [
        "--source",
        str(args.source),
        "--weights",
        str(args.weights),
        "--clip-manifest",
        str(args.clip_manifest),
        "--model-manifest",
        str(args.model_manifest),
        "--device",
        args.device,
        "--imgsz",
        "640",
        "--conf",
        "0.1",
        "--warmup-frames",
        str(args.warmup_frames),
        "--max-frames",
        str(args.max_frames),
    ]
    reference = measurements(load_rows(args.reference_detections))[: args.max_frames]
    runs = []
    report = {
        "schema_version": 1,
        "status": "running",
        "executable": str(executable),
        "source_sha256": digest(args.source),
        "weights_sha256": digest(args.weights),
        "reference_sha256": digest(args.reference_detections),
        "runs": runs,
        "protocol": {
            "repeats_per_mode": args.repeats,
            "warmup_frames": args.warmup_frames,
            "max_frames": args.max_frames,
            "batch_size": 1,
            "image_size": 640,
            "confidence": 0.1,
            "headless_comparison": True,
            "order": "detect/track, track/detect, alternating each pair",
            "timing": "Source PTS; synchronized CUDA inference; perf_counter durations",
            "includes": ["decode", "inference", "CPU tracking", "JSONL writes"],
            "excludes": ["startup", "loading", "checksums", "output finalization"],
        },
        "limitations": [
            "One short KITTI development sequence, not independent evaluation clips.",
            "No reference identities or tracking accuracy/ID-switch count.",
            "Paired overhead includes JSONL/statistics; track stage is isolated.",
            "GPU clocks/system load are uncontrolled; report short-run variability.",
            "H.264/JPEG preview is measured separately from the headless comparison.",
        ],
    }

    def execute(mode, name, extra=()):
        output = args.output / name
        command = [str(executable), mode, *common, "--output", str(output), *extra]
        start = perf_counter()
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        (args.output / f"{name}.log").write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f"{name} failed; see {name}.log")
        manifest = json.loads((output / "manifest.json").read_text())
        assert manifest["status"] == "complete"
        raw = load_rows(output / "detections.jsonl")
        assert len(raw) == len(reference) == args.max_frames
        assert measurements(raw) == reference
        assert manifest["metrics"]["frames_dropped"] == 0
        for artifact, expected in manifest["artifact_sha256"].items():
            assert digest(output / artifact) == expected
        item = {
            "mode": mode,
            "output": str(output),
            "command": command,
            "process_wall_s": perf_counter() - start,
            "model_load_s": manifest["model_load_s"],
            "tracking_load_s": manifest.get("tracking_load_s"),
            "metrics": manifest["metrics"],
            "manifest_sha256": digest(output / "manifest.json"),
            "artifact_sha256": manifest["artifact_sha256"],
        }
        if mode == "track":
            item["verification"] = verify_tracking(
                raw, load_rows(output / "tracks.jsonl"), manifest["tracking"]
            )
        print(
            f"{name}: {manifest['metrics']['warmed_processed_fps']:.2f} warmed FPS",
            flush=True,
        )
        return item

    try:
        for repeat in range(args.repeats):
            for mode in ["detect", "track"] if repeat % 2 == 0 else ["track", "detect"]:
                runs.append(execute(mode, f"{mode}-{repeat + 1}"))
        report["preview"] = execute(
            "track", "preview", ["--save-video", "--save-frames"]
        )
        from collision_warning.video import read_video

        decoded = read_video(args.output / "preview/tracking.mp4", "preview")
        count = 0
        try:
            for index, frame in enumerate(decoded):
                assert index < len(reference)
                expected = reference[index]["frame"]
                assert (
                    abs(
                        frame.info.timestamp_s
                        - (
                            expected["timestamp_s"]
                            - reference[0]["frame"]["timestamp_s"]
                        )
                    )
                    < 1e-6
                )
                assert frame.info.width == expected["width"] + expected["width"] % 2
                assert frame.info.height == expected["height"] + expected["height"] % 2
                count += 1
        finally:
            decoded.close()
        assert count == args.max_frames
        report["decoded_preview_frames"] = count
        report["all_measurements_match_phase1_reference"] = True
        report["summary"] = {}
        for mode in ["detect", "track"]:
            selected = [r for r in runs if r["mode"] == mode]
            report["summary"][mode] = {
                "warmed_fps": [r["metrics"]["warmed_processed_fps"] for r in selected],
                "median_warmed_fps": statistics.median(
                    r["metrics"]["warmed_processed_fps"] for r in selected
                ),
                "track_p50_ms": [
                    1000 * r["metrics"]["latency"]["track"]["p50_s"] for r in selected
                ],
                "track_p95_ms": [
                    1000 * r["metrics"]["latency"]["track"]["p95_s"] for r in selected
                ],
                "total_p95_ms": [
                    1000 * r["metrics"]["latency"]["total"]["p95_s"] for r in selected
                ],
            }
        report["status"] = "passed"
    except Exception as exc:
        report["status"] = "failed"
        report["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        (args.output / "acceptance.json").write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
