# Phase 2 milestone 1: CPU ByteTrack backend proof

This milestone selected and characterized an upstream backend. It did not add
tracking to `collision-warning`, implement histories or close Phase 2. The
decision and alternatives are in [ADR-0003](adr/0003-tracking-backend.md).
The subsequent owner request on 2026-10-17 added a standalone
[annotated tracking preview](tracking-preview.md) from saved detections, then
authorized the [domain adapter and live pipeline](tracking.md). The subsequent
[Phase 2 acceptance](phase2-acceptance.md) records the complete local gate.
The evidence below records the
earlier milestone-1 state, including its file hashes.

## Reproduce the synthetic proof

From the repository root, using Python 3.12 and the pinned uv version:

```bash
UV_PROJECT_ENVIRONMENT=.cache/phase2-tracking-cpu uv sync --locked --extra tracking
UV_PROJECT_ENVIRONMENT=.cache/phase2-tracking-cpu uv run --locked --extra tracking pytest -q -m tracking tests/integration/test_tracking_backend.py
```

Installation downloads locked upstream packages. Execution uses generated boxes,
scores and timestamps only. It needs no detector, weights, video, GPU or network.
Run this in a separate environment from the accepted GPU installation.

Default `uv sync --locked` and `make check` retain the ordinary CPU foundation.
The `tracking` marker is excluded by default, so collection needs no optional
imports. Explicitly selecting it without the extra produces an import failure;
it does not silently skip the backend proof. Hosted CI installs the extra and
runs this suite inside the required **CPU checks** job.

## Exact candidate artifacts

Inspected on 2026-10-16 using version-specific PyPI metadata, then SHA-256-verified
the complete upstream wheels before reading their source and license files.

| Package | Wheel SHA-256 | License |
| --- | --- | --- |
| [trackers 2.6.1](https://pypi.org/project/trackers/2.6.1/) | `b5188de630f449958be3ce787fbb0375c69cfde094b6e4b4329cd79a98108501` | Apache-2.0 |
| [supervision 0.30.9](https://pypi.org/project/supervision/0.30.9/) | `13468b993d60903cbc64ca956892fe47939bf5996f17fc052f262a023f80751a` | MIT |

The resolver-generated lock records exact artifact URLs and hashes, including
transitive dependencies. The [license ledger](third-party-licenses.md) distinguishes
this local engineering review from release-content clearance.

On this workstation, direct large-wheel transfers timed out. The complete SciPy
1.18.1 wheel was recovered from the existing pip HTTP download cache and verified
against the lock (`f55fa87b6c612ecd6b058f167c53231b1d14e412efe361d3d6e38b3631c73218`).
It was installed by pinned package requirement using `uv pip install --no-index
--no-deps --find-links`, followed by final `uv sync --locked --extra tracking`.
The environment was newly created from upstream wheel caches; no installed
baseline files were copied. The lock's official indexes and all existing package
records remain unchanged.

## What the tests establish

- Confirmation, repeated association and high/low/high score recovery.
- Unmatched low-score and below-activation candidates cannot seed tracks;
  activation threshold equality is checked explicitly.
- The backend itself will associate score-zero boxes if supplied. Our future
  adapter needs a configured low-score cutoff before backend invocation.
- Multiple identities survive reordered input/output; attached observation
  indices preserve the exact original boxes and scores without IoU rematching.
- Empty updates contain no measured boxes, while the separate prediction API
  may still expose a live track. Short gaps preserve backend identity; long gaps
  expire it, including when no intermediate frames were supplied.
- Source-time expiry, irregular intervals and nonzero timestamp origins.
- Class-agnostic matching, reset ID reuse and permissive timestamp warnings are
  characterized so later domain code can enforce stricter rules.
- A fresh interpreter can import/construct the backend with network connections
  blocked and without loading Torch, Torchvision or Ultralytics.

The fixture uses reference rate 10 Hz, a one-second buffer (`lost_track_buffer=30`),
two consecutive observations, activation threshold 0.6, high-score split 0.5 and
minimum association IoU 0.3. These explicit test settings are not road-scene tuning.

## Existing detections and later work

An offline evaluation can feed the already saved `detections.jsonl` to this backend
without rerunning YOLO. Preserve source seconds and observation indices, apply an
explicit low-score floor and use one tracker per class. Compare all returned
observations to their original records. Keep replay artifacts local with the
source JSONL hash; no source images are needed for association-only inspection.

A replay is an association smoke test. Bounded histories and continuity segments
are now implemented in milestone 2. The standalone preview supplies run-scoped IDs, a command,
run manifests and annotated video without completing milestone 3's full domain
integration. Pipeline throughput comparison
and recorded-video Phase 2 acceptance are milestone 4. Do not compare replay-only
CPU association timing to Phase 1 end-to-end CUDA throughput.

## Local results, 2026-10-16

All 19 real-backend cases passed, alongside 45 default CPU cases and three
generated-video cases. Fresh base setup, lint, formatting, mypy, pre-commit and
isolated base-wheel import/help checks passed. The wheel has no mandatory runtime
dependencies. Explicit tracking-test selection without the extra failed as
expected. Hosted CI is not claimed by these local checks.

The local replay used the same immutable 100-frame Phase 1 JSONL, SHA-256
`8cb8af31019f7aee20c2fe9d2a1d4b8c3e2137bd43c598b05fc6a35762d76648`,
with the fixture settings above and separate trackers per class:

| Replay | Input observations | Observations with confirmed backend IDs | Low-score observations associated |
| --- | --- | --- | --- |
| Detector floor 0.1 | 1,491 | 390 | 85 |
| High-score-only control, floor 0.5 | 362 | 294 | 0 |

The 0.1-floor input contains 1,129 observations below 0.5. Most weak detections do
not become confirmed associations under these settings. Every returned observation
index, box and score was checked against the input. The control illustrates the
effect of retaining weak measurements; these counts do not establish identity
accuracy or unique-object counts.

Ignored local artifacts are under `outputs/phase2-backend-proof/`: `replay.py`,
`replay-report.json` and `associations-{all,high-only}.jsonl`. The local script can
be rerun with `.cache/phase2-tracking-cpu/bin/python
outputs/phase2-backend-proof/replay.py` after choosing fresh output filenames; it
refuses to overwrite the recorded results. It is an evaluation artifact, not an
application command. Keep these KITTI-derived records local under the existing
development-data terms. The committed [evidence record](evidence/phase2-backend.json)
contains commands, hashes, limitations and environment/package preservation checks.
