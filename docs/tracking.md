# Video tracking and bounded observation histories

Phase 2 milestone 2 supplies a detector-independent `Tracker` protocol,
`ByteTrackAdapter`, immutable domain results and measurement-only history buffers.
The owner authorized this milestone on 2026-10-17. The existing
[`track-preview` command](tracking-preview.md) now consumes this shared adapter.
The live `track` command now runs detection and tracking in one pipeline, with
separate stage timings and optional annotated video. Phase 2 local acceptance is
recorded in [the acceptance report](phase2-acceptance.md); reference identity
accuracy remains unevaluated.

## Detect and track a video

Use a separate GPU environment with both optional extras; preserve the accepted
inference environment:

```bash
UV_PROJECT_ENVIRONMENT=.venv-tracking-gpu uv sync --locked --extra gpu --extra tracking --no-dev
.venv-tracking-gpu/bin/collision-warning track \
  --source data/external/kitti-0005-acceptance.mkv \
  --weights models/yolo11n.pt \
  --clip-manifest data/external/kitti-0005-acceptance.json \
  --model-manifest models/yolo11n.json \
  --device cuda:0 --imgsz 640 --conf 0.1 \
  --warmup-frames 10 --max-frames 100 \
  --save-video --save-frames \
  --output outputs/tracking-demo
```

The command writes unchanged detector measurements to `detections.jsonl`, original
observations/IDs/segments/lifecycle to `tracks.jsonl`, and run configuration,
versions, timing and artifact hashes to `manifest.json`. Optional previews are
`tracking.mp4` and `frame-*.jpg`; they render measured boxes with confirmed IDs,
leaving unassigned boxes gray. Run directories must be new. Missing inputs, bad
hashes, incompatible confidence floors and invalid CUDA devices fail explicitly;
runtime failures retain a manifest marked `failed` and close partial outputs.

`detect` and `track` share one pipeline and detector; `track` adds the independent
CPU adapter rather than using `YOLO.track()`. The detector confidence must be at
or below `--low-score` so inference does not remove the weak observations the
tracker is configured to consume. Defaults are both 0.1. Tracking currently
accepts timestamped video, while detection retains image/directory support.

Omit preview flags for a headless run. Both commands report source-time range,
zero intentionally dropped frames, cold first-frame latency, warmed throughput
and p50/p95 stage durations. Stages include decode, synchronized detection,
tracking, preview and serialization. `output` includes output bookkeeping,
rendering and JSONL serialization; `preview` and `serialize` are components of
that output stage, not additional terms to add to it. Frame totals exclude
loading, input checksums, preview finalization, artifact hashing and final manifest
writing; those boundaries are explicit in the acceptance report.

## Use the adapter

Install the pinned `tracking` extra in a separate CPU environment. No video,
weights, images or inference framework is needed to associate domain detections:

```python
from collision_warning.domain import Detection, FrameInfo
from collision_warning.tracking import ByteTrackAdapter, TrackingConfig

tracker = ByteTrackAdapter(
    TrackingConfig(
        history_max_observations=30,
        history_max_seconds=2.0,
    )
)
for index, score in enumerate([0.9, 0.9, 0.18]):
    frame = FrameInfo("example", index, 5.0 + index / 10, 640, 480)
    detection = Detection(frame, 2, "car", score, (100, 100, 200, 240))
    result = tracker.update(frame, [detection])
    for track in result.tracks:
        print(track.identity.value, track.state, track.segment_id, track.history)
```

Call `update(frame, [])` for an empty frame. Supply `FrameInfo` and detections
only; the adapter never receives or retains pixel arrays. Timing always uses
source seconds, including nonzero origins and irregular frame intervals.
`frame_rate` is backend reference metadata, not a replacement clock.

## Domain results

| Value | Meaning |
| --- | --- |
| `TrackIdentity` | Namespace, epoch, source, class and backend ID; `.value` is `namespace/epoch/class/backend` |
| `TrackedDetection` | Original detection, input index, optional identity/segment and status |
| `Track` | Immutable observed/lost snapshot with a tuple of original detections in the current segment |
| `TrackEnd` | Identity ended by expiry, reset or discontinuity, with its reason |
| `TrackingResult` | Frame, input observations in order, live tracks, ended tracks and optional reset reason |

Statuses are `associated`, `unassigned` and `below_floor`. Confirmation requires
two backend observations; tentative/unassigned observations are returned but
are not backfilled into a confirmed history. Per-class instances prevent
cross-class association. Equal backend numbers in different classes identify
separate tracks.

Quality fields are inspectable counts/times, not calibrated probabilities:

- `age_s`: source time since the first confirmed observation.
- `time_since_observed_s`: zero while observed, increasing during loss.
- `observations_seen`: confirmed observations across this identity's segments.
- `consecutive_observations`: adjacent confirmed observations in this segment,
  zero while lost.
- Original detector scores remain attached to retained measurements.

## Lifecycle and continuity

An empty or unassigned update makes a previous track `lost`. No measurement is
appended. On reacquisition of that backend ID, `segment_id` increments and the
old history is cleared before appending the new observation. Numerical consumers
therefore cannot join across a dropout merely because a backend retained its ID.

Once its last confirmed observation is older than the effective lost buffer,
a track emits `TrackEnd(reason="expired")` and is removed from retained domain
state, even on empty frames. ByteTrack also applies its own source-time budget
before matching.

The adapter discards backend/history state and advances its namespace epoch for:

| Trigger | Reset reason |
| --- | --- |
| Source ID change, allowing a new clock/index origin | `source_changed` |
| Resolution change within an increasing source | `resolution_changed` |
| Skipped frame indices | `frame_gap` |
| Updates farther apart than `max_gap_seconds` | `time_gap` |
| Explicit `reset()` | `manual_reset` |

Automatic resets include ended identities in the result. Explicit `reset()`
returns those events directly and advances the epoch even when empty. New
adapters generate UUID namespaces; callers supplying their own namespace must
keep it unique across persisted runs/streams.

Within one source, duplicate/backward indices or timestamps fail before mutation,
including when resolution changes. Detection/frame mismatches and invalid index
or class types also fail before mutation. Backend mapping/measurement failures
raise and invalidate the partially updated epoch; the next update starts fresh.
A failed update has no result to publish, so its caller must record the failure.

Class changes create a separate partition and never mix histories. The old class
may remain lost until expiry. IDs remain hypotheses: this does not detect every
identity switch caused by overlap or occlusion.

## Retention limits

Defaults retain at most **30 observations and 2 source seconds per live track**,
applying both limits. Pruning runs on every accepted frame, including lost tracks.
A history can become empty before its identity expires if its time window is
shorter than the lost buffer. Only metadata is retained for ordering after the
buffer becomes empty.

Histories contain original immutable `Detection`/`FrameInfo` values, never decoded
`Frame` objects, images, predictions or synthesized observations. Results are
immutable snapshots that remain stable as buffers advance. Limits bound the
adapter's retained history per live track; consumers retaining older snapshots
own that additional memory.

`history_max_observations` is a positive integer; `history_max_seconds` is finite
and positive. Association thresholds are unchanged. Lost time defaults to one
second, rounded to backend units of 1/30 second; `effective_lost_seconds` records
the actual value. The independently configurable stream gap limit defaults to
one second.

Preview options are `--history-max-observations`, `--history-max-seconds` and
`--max-gap-seconds`. JSONL stores each observation once with `track_id` and
`segment_id`, plus live-track summaries, history sizes/time bounds and end/reset
events. It does not duplicate full history tuples every frame. Complete bounded
tuples are available through the Python API.

## Verification

```bash
UV_PROJECT_ENVIRONMENT=.cache/phase2-tracking-cpu uv sync --locked --extra tracking --extra video
UV_PROJECT_ENVIRONMENT=.cache/phase2-tracking-cpu uv run --locked --extra tracking --extra video pytest -q -m tracking tests/integration/test_tracking_backend.py tests/integration/test_tracking_adapter.py tests/integration/test_tracking_preview.py
```

Default CPU tests also run `tests/unit/test_tracking_history.py` without optional
imports. Tests cover independent count/time limits, immutable snapshots,
pre-mutation rejection, original observations after backend reordering, weak-score
association, loss/reacquisition/expiry, reset/source namespaces, class partitions,
irregular times and partial backend failure. Generated-video tests exercise the
shared adapter through the preview command.

Earlier saved-detection replay is recorded in
[milestone-2 evidence](evidence/phase2-tracking-adapter.json); completed live-video
validation and matched throughput measurements are in
[Phase 2 evidence](evidence/phase2-tracking.json). There are no
velocity/TTC/range/warning estimators or reference identity metrics. See
[ADR-0004](adr/0004-tracking-lifecycle.md) and the
[feature plan](detection-tracking-plan.md).
