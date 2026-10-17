# Phase 2 acceptance: live tracking, histories and video

Local acceptance passed on 2026-10-17 using the built wheel installed in a new
combined GPU/tracking environment. Required hosted CPU checks and protected PR
integration are separate gates recorded in [the evidence](evidence/phase2-tracking.json).
No TTC, distance, path-overlap or collision-warning logic was introduced.

## What was verified

- The full `track` command decodes the existing 100-frame KITTI development video,
  runs YOLO11n on CUDA and associates its measurements with the CPU ByteTrack
  adapter in one pipeline. Every detection in all runs matches the Phase 1
  reference exactly; no frames are intentionally dropped.
- Three headless repetitions per mode use the same source, weights, 640 input,
  confidence 0.1, selected COCO classes, batch one, FP32, ten warm-up frames,
  installation and GPU. Pair order alternates. Tracking writes its additional
  JSONL; preview export is disabled in both comparison modes.
- Each tracking run associates 390 of 1,491 observations, including 85 low-score
  observations. These are assignments, not unique-object counts or accuracy.
  Histories obey count/source-age limits and never receive predicted boxes.
- An additional full tracking run writes 100 annotated JPEGs and an H.264 MP4.
  All 100 decoded preview frames retain source intervals within one microsecond;
  playback starts at zero. The original 1242×375 image is padded to 1242×376.
- Existing output, wrong model hash, missing source, invalid CUDA device, corrupt
  video and an incompatible detector/tracker floor all fail as expected.
  Partial runs are marked failed; accepted files and GPU environments are preserved.

## Measurements

RTX 5070 Ti, compute capability 12.0, PyTorch 2.14.1+cu130, CUDA build 13.0,
Ultralytics 8.4.172, trackers 2.6.1 and supervision 0.30.9. Each warmed summary
contains 90 frames. CUDA synchronization surrounds inference; association uses
source timestamps. Time is measured with `perf_counter`.

| Mode | Warmed FPS, repetitions 1 / 2 / 3 | Track p50, ms | Track p95, ms |
| --- | --- | --- | --- |
| Detection only | 44.85 / 42.02 / 68.89 | 0 / 0 / 0 | 0 / 0 / 0 |
| Detection + tracking | 41.04 / 68.24 / 54.44 | 0.548 / 0.526 / 0.532 | 0.667 / 0.666 / 0.710 |

The separate tracking run with JPEG/H.264 export processed 29.25 warmed FPS.
Preview export uses a different output workload, so its timing is not the matched
headless comparison. Per-run loading, cold-frame, decode, detection, tracking,
preview, serialization, total p50/p95 and throughput values are in the evidence.

Tracking itself adds about 0.53 ms at the per-run median, with per-run p95 below
0.71 ms. End-to-end throughput varies strongly, including a tracking run faster
than its paired baseline. GPU clocks and system load were uncontrolled, so these
short runs do not establish a reliable net FPS penalty or a tracking speedup.
The earlier 30-FPS aspiration remains a target, not a validated sustained guarantee.

Frame timing includes decoding, inference, optional tracking, output bookkeeping
and JSONL writes, plus preview work when enabled. It excludes process startup,
model/backend loading, checksum verification, final encoder flush, artifact
hashing and final manifest writing. Process wall time is reported separately.

## Continuity inspection

The script finds candidate examples automatically. Visual inspection covered
frames 1, 22, 24, 50 and 99 of the final live preview:

- Person `#0:1` remains associated through frames 1–99 and visually follows the
  striped-shirt cyclist as the camera advances. Its retained window stays bounded.
- Bicycle `#1:0` has an adjacent-observation segment through frames 1–56. Person
  and bicycle boxes overlap because the detector supplies both hypotheses.
- Car `#2:0` follows the white van in frames 22 and 24. Frame 23 lacks its confirmed
  assignment, so reacquisition starts segment 1 instead of joining the histories.
- Labels remain crowded on overlapping weak boxes. Detector class ambiguity and
  backend identity switches are still possible; no reference identities were
  acquired, so no ID-switch accuracy, IDF1 or HOTA result is claimed.

## Reproduce

After installing the pinned combined environment and providing the local assets
with the provenance cards in the [tracking guide](tracking.md):

```bash
.venv-tracking-gpu/bin/python scripts/accept_tracking.py \
  --source data/external/kitti-0005-acceptance.mkv \
  --weights models/yolo11n.pt \
  --clip-manifest data/external/kitti-0005-acceptance.json \
  --model-manifest models/yolo11n.json \
  --reference-detections outputs/phase1-clean-gpu-acceptance/gpu-1/detections.jsonl \
  --output outputs/phase2-acceptance-new
```

The script refuses existing output, runs the installed environment's console
script, compares every original measurement, checks tracking lifecycle/history
summaries and decodes the resulting preview. Each subprocess log and its exact
arguments remain with the local run. The acceptance record is written even if
an assertion fails; failed results must not be reported as passing evidence.

On this workstation, artifacts live under ignored `outputs/phase2-acceptance/`:
`detect-{1,2,3}`, `track-{1,2,3}`, `preview`, `acceptance.json` and failure checks.
The source is the same KITTI drive_0005/image_02 development sequence accepted in
Phase 1, not independent held-out footage. Its CC-BY-NC-SA-3.0 provenance,
attribution and local noncommercial-use terms remain in every run manifest.
Raw and derived media are not committed or published.
