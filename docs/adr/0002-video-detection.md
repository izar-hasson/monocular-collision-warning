# ADR-0002: Timestamped video and an explicit detector boundary

Status: accepted for implementation, 2026-10-05; phase acceptance remains evidence-gated.

## Context

Phase 0 is complete and the owner has requested detection and tracking. Later
motion estimators need source time and original-pixel observations, independent
of detector identity, processing speed and rendering. The previous CUDA demo
works and must remain intact while the project integration is verified.

## Decision

Decode local video with PyAV and preserve `pts * time_base`. Do not normalize
nonzero origins or infer missing timestamps from FPS. Reject timestamp regressions
and missing timestamps so future motion cannot silently consume invented time.

Use immutable `FrameInfo` and `Detection` values. Pixels are uint8 BGR, boxes are
original-resolution xyxy pixels; finite ordered boxes are clipped to image bounds,
fully outside boxes are omitted and malformed boxes fail the run. Detector scores
remain detector scores.

Use a `Detector` protocol and lazy `YoloDetector` adapter. Start with the existing
Ultralytics 8.4.172 / YOLO11n candidate rather than changing model families. Require
explicit local `.pt` weights and a matching SHA-256 before construction. Keep
model/data source and rights in separate input manifests. No model aliases or
downloads at package import/test time.

The base package remains dependency-free. On 2026-10-06 the owner authorized
PyAV installation and reusing the production reader in the checkout test script.
The locked `video` extra supplies PyAV/NumPy; the optional `gpu` extra now pins the working YOLO/cu130 baseline, with
verification required in a separate `.venv-gpu`. Generated-PyAV tests are opt-in (`slow`). The checkout script
reuses the existing YOLO environment for inference and OpenCV for visualization,
while video input uses `video.read_video` and its presentation-timestamp contract.
Its KITTI sequence reader preserves the supplied timestamps.
The GPU lock uses explicit cu130 torch and torchvision mappings and baseline
transitive constraints. The sibling working environment remains preserved.

Default road-user classes are COCO IDs 0, 1, 2, 3, 5, 7; this mapping applies to
the candidate COCO model and must be changed for a model with different classes.
Confidence 0.1 retains candidate detections for Phase 2's low-score association.
These are initial configuration choices, not tuned detection/risk thresholds.

Write streaming JSONL plus a run manifest. Separate model loading, first frame,
warm-up and warmed stage timings; synchronize CUDA around inference. Output has
no TTC, distance or warning field. ByteTrack will consume domain detections after
the detection gate and never trigger another detector call.

## Consequences

The video dependency adds a bundled FFmpeg license review. The YOLO adapter and
weights carry upstream AGPL/enterprise terms; no source license is selected by
this ADR. Local experimental use and a public release are separate decisions.
Missing timestamps fail explicitly. Source-rate and throughput measurements are
distinct. Real clip/model behavior needs local evidence beyond CPU fake tests.

Sources reviewed: [PyAV time](https://pyav.org/docs/stable/api/time.html),
[Ultralytics prediction](https://docs.ultralytics.com/modes/predict/),
[uv/PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/),
[Ultralytics terms](https://www.ultralytics.com/license).
