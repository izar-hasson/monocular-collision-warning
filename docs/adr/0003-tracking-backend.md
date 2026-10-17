# ADR-0003: A pinned, independent CPU ByteTrack backend

Status: accepted for Phase 2 milestone 1, 2026-10-16. Application integration and
Phase 2 acceptance remain pending. [ADR-0004](0004-tracking-lifecycle.md) records
the subsequently authorized adapter/history implementation.

## Context

Phase 1 merged through PR #7 (`4049432`). The owner authorized only Phase 2's
first milestone: select a CPU backend, pin its dependencies, characterize actual
association behavior with synthetic tests, and document the decision. The
existing detector, CLI, observations and GPU environments must remain usable.

## Decision

Select `trackers==2.6.1`, specifically `trackers.ByteTrackTracker`, with
`supervision==0.30.9` for its detection container. Inspect the exact published
wheels, rather than relying on a moving development documentation page. Record
their URLs, hashes, license files and observed behavior in the
[backend guide](../tracking-backend.md) and evidence record.

Install them only through an optional `tracking` extra. Pin shared NumPy 2.5.2
and opencv-python 5.0.0.93 to the accepted inference baseline. Resolve the other
dependencies in `uv.lock` without upgrading previously locked packages or
changing the explicit PyTorch index. Do not install detection, mask or tuning
extras. The base package stays dependency-free; tracking tests need no model,
GPU, media or network at execution time.

Add a dedicated real-backend CPU test step to the existing required CI job.
Default tests exclude the `tracking` marker and still collect without the extra;
explicit selection must fail if the extra is missing, rather than silently skip.

## Backend behavior and obligations for the later adapter

- Explicit scores are essential. Missing scores are treated as fully confident.
- High-score matches precede low-score association. There is no low-score floor
  in this backend: the later adapter must apply and validate an explicit floor.
  The initial detector floor is 0.1; the smoke script's 0.25 default must not be
  silently used for low-score tracking experiments.
- New detections are initially returned with ID `-1`. Our characterization uses
  two observations for confirmation. Unmatched detections below the activation
  threshold do not create tracks. Confirmation rules and thresholds are research
  configuration, not tuned road-user accuracy claims.
- Output may be reordered. Attach a per-frame observation index through
  `Detections.data`; recover the original domain `Detection` by that index.
  `update()` returns original detection boxes, while `tracked_objects` contains
  Kalman predictions, including unmatched tracks. Never use that latter API as
  measured history.
- Association ignores class labels. The later adapter will partition by class,
  accepting fragmentation when the detector alternates car/truck/bus classes.
  Include class in the identity namespace as backend instances allocate locally.
- Pass source seconds on every update, including empty frames. Version 2.6.1
  supports `timestamp=`, scales prediction by elapsed time and expires tracks by
  elapsed seconds. A buffer of 30 corresponds to one second, not 30 source frames
  in this mode. Record the reference frame rate as well as the timestamp basis.
- Non-finite/backward timestamps warn and skip; duplicate timestamps warn but
  still associate. The future adapter must reject these before backend mutation,
  preserving this project's strictly increasing timestamp contract.
- `reset()` clears tracks and restarts numeric IDs. A future adapter must
  namespace IDs across resets and sources, and break continuity on reacquisition.

These obligations are documented now; this milestone does not implement an
adapter, histories, application tracking command or tracking preview.

## Alternatives

| Candidate | Evaluation | Decision |
| --- | --- | --- |
| Roboflow Trackers 2.6.1 | Python >=3.10; independent NumPy/SciPy association, source-time support, original observation indexing; Apache-2.0 wheel license | Selected; actual CPU behavior tested |
| Supervision 0.30.9 `ByteTrack` | Exact wheel marks it deprecated since 0.28.0 for removal in 0.31.0, directing users to Trackers; frame-step API | Rejected as our association backend; retain only its detection container |
| Existing Ultralytics 8.4.172 `BYTETracker` | Exact installed source exposes association separately, but imports Ultralytics utilities and adds inference-framework coupling to CPU setup | Deferred; do not use `YOLO.track()` or change the detector boundary |
| Original FoundationVision ByteTrack | Reference algorithm and research implementation, coupled to the YOLOX project layout | Reference only; avoid vendoring or maintaining a fork for this milestone |

## Consequences

The selected package has a broader CPU dependency closure than association alone:
Supervision, SciPy, OpenCV, PyAV, plotting and terminal utilities. Keep these
optional and record exact license/notice evidence. Synthetic association tests
characterize this implementation; they do not establish equality with the paper,
recorded-video identity accuracy or the throughput of our eventual pipeline.

Source license selection and any binary/model/media redistribution remain
separate decisions. No external implementation is copied into our source tree.

## Primary sources

- [Trackers 2.6.1 release metadata](https://pypi.org/pypi/trackers/2.6.1/json)
  and its published wheel's `trackers/core/bytetrack/tracker.py`,
  `trackers/core/base.py` and Apache-2.0 license.
- [Supervision 0.30.9 release metadata](https://pypi.org/pypi/supervision/0.30.9/json)
  and its wheel's `supervision/tracker/byte_tracker/core.py` and MIT license.
- [Original ByteTrack publication](https://arxiv.org/abs/2110.06864) and
  [reference implementation](https://github.com/FoundationVision/ByteTrack).
