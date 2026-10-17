# Annotated tracking video from saved detections

`track-preview` reuses a completed detection run and its original video. It runs
the pinned ByteTrack backend on CPU, without loading YOLO, weights or CUDA.
It now uses the shared [tracking adapter and bounded histories](tracking.md).
Use Python 3.12 and the repository's pinned uv version, in a separate environment:

```bash
UV_PROJECT_ENVIRONMENT=.cache/phase2-tracking-cpu uv sync --locked --extra tracking --extra video
UV_PROJECT_ENVIRONMENT=.cache/phase2-tracking-cpu uv run --locked --extra tracking --extra video collision-warning track-preview \
  --source data/external/kitti-0005-acceptance.mkv \
  --detection-run outputs/phase1-clean-gpu-acceptance/gpu-1 \
  --output outputs/phase2-tracking-preview
```

Choose a new output directory for each run. `--detection-run` must contain the
existing `manifest.json` and `detections.jsonl`, as written by `detect` or the
shared detection test script. The detection run must have completed and its
source checksum must match the supplied video. Image-directory runs are not
supported by this video command. All input files remain unchanged.

The command writes:

| File | Contents |
| --- | --- |
| `tracking.mp4` | H.264 video with colored confirmed IDs and gray unassigned boxes |
| `tracks.jsonl` | Original observations with ID/segment assignments, live-track summaries and ended/reset events |
| `manifest.json` | Completion/failure, source and input hashes, configuration, versions, counts and artifact hashes |

Open `tracking.mp4` in a video player. For WSL, from the repository root:

```bash
explorer.exe "$(wslpath -w outputs/phase2-tracking-preview/tracking.mp4)"
```

Colored labels such as `car #2:0 0.82` show the detector class, class-scoped backend
ID and detection confidence. `#2:0` and `#0:0` are different identities. Gray
`unassigned` boxes include tentative tracks and observations below the low-score
floor. All saved detections remain visible. An ID appears only after the backend
confirms it; it is an association hypothesis, not a verified physical identity.

Playback starts at zero and preserves source frame intervals at microsecond
precision. JSONL retains the original absolute source timestamps. Odd dimensions
are padded at the right/bottom for H.264, without moving detection coordinates.
Source audio is omitted. The output contains the detection run's recorded video
prefix, which can be shorter than the full source.

## Association settings

| Option | Default | Meaning |
| --- | --- | --- |
| `--low-score` | `0.1` | Explicit minimum confidence supplied to ByteTrack |
| `--high-score` | `0.5` | Split between first-stage and second-stage detections |
| `--activation-score` | `0.6` | Minimum confidence to seed a track |
| `--minimum-iou` | `0.3` | Backend minimum association IoU |
| `--lost-seconds` | `1.0` | Lost-track buffer, rounded to the backend's 1/30-second units |
| `--max-gap-seconds` | `1.0` | Reset tracking after a larger source-time gap |
| `--history-max-observations` | `30` | Maximum retained measurements per live track |
| `--history-max-seconds` | `2.0` | Maximum source age of retained measurements |

Require `0 <= low <= high <= activation <= 1`. Confirmation requires two
consecutive observations. Settings reproduce the backend proof; they have not
been tuned or validated as optimal road-scene parameters. Lowering the tracking
floor cannot recover detections already removed during inference.

The preview uses separate backends per class and source timestamps on every
frame, including empty updates. It maps returned observation indices to original
boxes/scores and checks they were not changed. Only measured boxes are rendered;
empty frames contain no predicted boxes. JSONL IDs use `namespace/epoch/class/id`,
preventing reuse across runs and resets. Reacquisition starts a new continuity
segment and clears its prior history. JSONL records history sizes and time bounds
without copying entire history tuples each frame. Invalid frame
indices, timestamps, dimensions, observation bounds or counts fail the run;
failures after output creation leave a manifest marked `failed`.

This preview capability and the subsequent domain adapter/history milestone were
authorized on 2026-10-17. The subsequent `track` command and
[Phase 2 acceptance](phase2-acceptance.md) complete the live pipeline and measured
development-video gate. Reference identity accuracy is unevaluated. Class changes fragment identities;
occlusion, crowded boxes and ID switches still require review. No velocity, TTC,
metric range or warning is inferred. See [ADR-0003](adr/0003-tracking-backend.md)
for backend behavior and [the feature plan](detection-tracking-plan.md) for the
remaining work.

## Verification

```bash
UV_PROJECT_ENVIRONMENT=.cache/phase2-tracking-cpu uv run --locked --extra tracking --extra video pytest -q -m tracking tests/integration/test_tracking_backend.py tests/integration/test_tracking_adapter.py tests/integration/test_tracking_preview.py
```

Tests use generated lossless video and actual CPU association/encoding. They
check per-class IDs, weak-score recovery, empty frames, expiration, original
measurement mapping, decoded playback timestamps, odd-height padding, source
checksums, existing-output protection, malformed/misaligned records and prefix
runs. Optional imports remain lazy so ordinary help and base tests require no
tracking/video packages. The required hosted CPU job explicitly runs this suite.

The local KITTI preview processed 100 frames and all 1,491 saved observations:
390 received confirmed IDs, including 85 low-score observations; 1,101 were
unassigned. These are assignment counts, not unique-object or accuracy metrics.
The [preview evidence](evidence/phase2-tracking-preview.json) records validation
of the earlier preview implementation. The shared-adapter replay is under
`outputs/phase2-history-preview/`; its [milestone-2 evidence](evidence/phase2-tracking-adapter.json)
records the current lifecycle/history verification. Raw and derived media stay ignored/local under the source
manifest's KITTI terms and attribution.
