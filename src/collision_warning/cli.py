"""Console entry points; optional inference dependencies load only for a run."""

import argparse
from collections.abc import Sequence
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

from collision_warning.detection import DetectorConfig
from collision_warning.tracking import TrackingConfig


def add_detection_arguments(
    parser: argparse.ArgumentParser, *, smoke: bool = False
) -> None:
    """Share run options; the smoke entry point supplies convenient local defaults."""
    parser.add_argument(
        "--source", type=Path, required=True, help="Video, image, or KITTI directory"
    )
    parser.add_argument(
        "--weights", type=Path, required=True, help="Existing local .pt weights"
    )
    parser.add_argument("--clip-manifest", type=Path, required=not smoke)
    parser.add_argument("--model-manifest", type=Path, required=not smoke)
    parser.add_argument(
        "--output", type=Path, required=not smoke, help="New output directory"
    )
    parser.add_argument("--device", default="cpu", help="cpu or cuda:N")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.25 if smoke else 0.1)
    parser.add_argument("--classes", nargs="+", type=int, default=[0, 1, 2, 3, 5, 7])
    parser.add_argument("--warmup-frames", type=int, default=5)
    parser.add_argument("--max-frames", type=int, default=100 if smoke else None)
    parser.add_argument(
        "--save-video", action="store_true", help="Save annotated video for video input"
    )
    parser.add_argument(
        "--save-frames",
        action=argparse.BooleanOptionalAction,
        default=smoke,
        help="Save annotated JPEG frames",
    )
    parser.add_argument(
        "--expected-sha256", help="Independent expected weights checksum"
    )


def add_tracking_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--low-score", type=float, default=0.1)
    parser.add_argument("--high-score", type=float, default=0.5)
    parser.add_argument("--activation-score", type=float, default=0.6)
    parser.add_argument("--minimum-iou", type=float, default=0.3)
    parser.add_argument("--lost-seconds", type=float, default=1.0)
    parser.add_argument("--max-gap-seconds", type=float, default=1.0)
    parser.add_argument("--history-max-observations", type=int, default=30)
    parser.add_argument("--history-max-seconds", type=float, default=2.0)


def tracking_config(args: argparse.Namespace) -> TrackingConfig:
    return TrackingConfig(
        low_score=args.low_score,
        high_score=args.high_score,
        activation_score=args.activation_score,
        minimum_iou=args.minimum_iou,
        lost_seconds=args.lost_seconds,
        max_gap_seconds=args.max_gap_seconds,
        history_max_observations=args.history_max_observations,
        history_max_seconds=args.history_max_seconds,
    )


def execute_detection(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    """Wire parsed options to the same run implementation for both entry points."""
    from collision_warning.run import detect_source

    output = args.output or Path("outputs") / f"detection-test-{uuid4().hex[:8]}"
    try:
        config = DetectorConfig(args.device, args.imgsz, args.conf, tuple(args.classes))
        result = detect_source(
            args.source,
            args.weights,
            args.clip_manifest,
            args.model_manifest,
            output,
            config,
            warmup_frames=args.warmup_frames,
            max_frames=args.max_frames,
            expected_sha256=args.expected_sha256,
            save_frames=args.save_frames,
            save_video=args.save_video,
            tracking_config=tracking_config(args)
            if getattr(args, "command", None) == "track"
            else None,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        name = "Tracking" if getattr(args, "command", None) == "track" else "Detection"
        parser.exit(1, f"{name} failed: {exc}\n")
    print(f"Processed {result['metrics']['frames_processed']} frames: {output}")
    print(f"Detections by class: {result['metrics']['class_counts']}")
    return 0


def detection_test_main(argv: Sequence[str] | None = None) -> int:
    """Run local smoke inputs through the package runner with optional previews."""
    parser = argparse.ArgumentParser(description="Test the shared detection pipeline.")
    add_detection_arguments(parser, smoke=True)
    return execute_detection(parser.parse_args(argv), parser)


def main(argv: Sequence[str] | None = None) -> int:
    """Display help/version or run detection on a provenance-checked local input."""
    parser = argparse.ArgumentParser(
        prog="collision-warning",
        description="Offline monocular RGB collision-warning research prototype.",
        epilog=(
            "Current status: Phase 2 video detection and tracking. "
            "Research use only; not a certified automotive safety system."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('monocular-collision-warning')}",
    )
    commands = parser.add_subparsers(dest="command")
    detect = commands.add_parser("detect", help="Detect road users in a local input")
    add_detection_arguments(detect)
    track = commands.add_parser(
        "track", help="Detect and track road users in a local video"
    )
    add_detection_arguments(track)
    add_tracking_arguments(track)
    preview = commands.add_parser(
        "track-preview",
        help="Annotate a video using a saved detection run and CPU ByteTrack",
    )
    preview.add_argument(
        "--source", type=Path, required=True, help="Original source video"
    )
    preview.add_argument(
        "--detection-run",
        type=Path,
        required=True,
        help="Completed run containing manifest.json and detections.jsonl",
    )
    preview.add_argument(
        "--output", type=Path, required=True, help="New output directory"
    )
    add_tracking_arguments(preview)
    args = parser.parse_args(argv)
    if args.command in {"detect", "track"}:
        return execute_detection(args, parser)
    if args.command == "track-preview":
        from collision_warning.tracking_preview import (
            track_preview,
        )

        try:
            result = track_preview(
                args.source,
                args.detection_run,
                args.output,
                tracking_config(args),
            )
        except (OSError, ValueError, RuntimeError) as exc:
            parser.exit(1, f"Tracking preview failed: {exc}\n")
        print(
            f"Annotated {result['frames_processed']} frames: "
            f"{args.output / 'tracking.mp4'}"
        )
        return 0
    parser.print_help()
    return 0
