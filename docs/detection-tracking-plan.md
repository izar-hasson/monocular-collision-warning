# Detection and tracking implementation plan

Owner authorization: 2026-10-05. Phase 0 is complete. This request starts
Phase 1 (video/detection), followed by Phase 2 (tracking); phases 3–7 remain
outside this change. No phase is complete merely because its code exists.

Update 2026-10-12: the [original acceptance evidence](evidence/phase1-detection.json)
records three installed-CLI CUDA runs on one 100-frame KITTI development sequence,
verified timestamps/artifacts, failure handling, visual review and measured
latency/FPS. These extend the October 6 CPU image/12-frame/video smoke checks.
The [closure evidence](evidence/phase1-closure.json) records fresh GPU reconstruction
from complete verified upstream wheels, final locked sync and three additional
passing CUDA repetitions with identical observations/previews. The documented
GPU-only CDN/cache fallback resolves this workstation's index-host timeout
without copying installed baseline files or changing the lock. Phase 1 acceptance
is complete; PR #7 subsequently merged as `4049432`.

Update 2026-10-16: the owner authorized only Phase 2 milestone 1. Select and pin
an independent CPU ByteTrack backend, characterize its actual association behavior,
and document the decision. See [ADR-0003](adr/0003-tracking-backend.md) and the
[backend guide](tracking-backend.md). This does not authorize the remaining
adapter/history, application integration or video/performance milestones.

Update 2026-10-17: the owner requested annotated tracking video. A standalone
`track-preview` command now replays saved detection runs on CPU, writes measured
boxes with class-scoped IDs to H.264 MP4 and records assignments/provenance. See
the [preview guide](tracking-preview.md). This narrow addition brings forward
preview inspection; it does not complete domain histories, continuity segments,
full application tracking or Phase 2 accuracy/performance acceptance.

Subsequent authorization, 2026-10-17: implement milestone 2's domain adapter,
lifecycle and bounded observation histories. The [shared adapter](tracking.md)
now implements those contracts and is consumed by the preview. Local evidence
is in [phase2-tracking-adapter.json](evidence/phase2-tracking-adapter.json).
That record captures the milestone-2 state before full orchestration.

Finalization authorization, 2026-10-17: complete Phase 2. The shared `track` command
now orchestrates detection/tracking/output; local acceptance passed with a newly
installed wheel, three matched GPU repetitions per mode, real annotated video,
continuity inspection and failure checks. [The acceptance report](phase2-acceptance.md)
records timing variability without claiming reference identity accuracy. Hosted
checks/protected integration are recorded in [final evidence](evidence/phase2-tracking.json).

## Phase 1

1. Add immutable frame/detection contracts with source presentation time in
   seconds, BGR pixels, finite pixel boxes, and explicit bounds validation.
2. Decode a local video using PyAV. Preserve `pts * time_base`, including
   irregular intervals and nonzero origins. Reject missing or non-increasing
   timestamps rather than deriving motion time from nominal FPS.
3. Wrap the already-tested Ultralytics version behind a detector protocol.
   Load only an explicit local detection model after SHA-256 verification;
   translate original-resolution boxes and class names into domain values.
4. Add `collision-warning detect`, JSONL observations, and a run manifest
   recording input/model hashes, config, versions and stage timings. Separate
   cold start and warm-up from warmed measurements. Synchronize CUDA timing.
5. Keep default CPU tests free of models/GPU/network. Exercise fake model output,
   empty scenes, malformed input and generated variable-timestamp video.
6. Obtain a small research-authorized driving sequence, record provenance and
   sequence split, and run the real detector. Keep raw/derived media outside Git.
7. Verify a separate locked GPU environment before replacing any baseline.

Phase 1 gate: passing CPU checks, decoded timestamps verified against the source,
real-model driving-video observations/artifacts with provenance, and measured
latency/FPS with declared hardware/config. No detection-accuracy claim without
reference boxes. Hosted CPU checks are still required before a merge.

## Phase 2

Deliver sequentially: (1) backend selection and real synthetic CPU proof,
(2) domain tracking adapter/lifecycle/bounded histories, (3) application command,
outputs and previews, and (4) recorded-video continuity/performance acceptance.
All four milestones passed local implementation/acceptance checks, including the
live shared pipeline and matched video/performance report. Protected integration
still requires the hosted CPU checks; standalone replay alone was not closure.

After the Phase 1 gate, feed detections to an independent ByteTrack adapter.
Do not combine inference and tracking through `YOLO.track()`: a future detector
must be replaceable without replacing history or tracking.

- Preserve low-confidence detections for ByteTrack's second association stage.
- Maintain bounded observation histories using source timestamps.
- Emit observed tracks and explicit gaps; never append predicted boxes as
  measurements. Stable IDs indicate an association hypothesis, not proof.
- Reset on source/resolution changes, discontinuities and long gaps. Namespace
  identities across resets so reused upstream IDs cannot join old histories.
- Clear continuity on class changes, reacquisition gaps and identity changes;
  do not expose velocity/TTC in these phases.
- Test identity continuity, empty frames, short/long dropouts, new identities,
  stream changes, time ordering and history limits with synthetic detections.
- Repeat the same driving clip with tracking enabled; review ID examples and
  measure tracking stage time and throughput against detection-only output.

Phase 2 gate: CPU contracts/tests, actual ByteTrack synthetic association checks,
recorded-video continuity examples and measured throughput impact. Recorded-video
examples establish behavior, not ID-switch accuracy without reference IDs.

## Dataset selection

The handoff names discovery directories, not an acquired dataset. Roboflow
Universe's example dashcam datasets primarily expose extracted images; shuffled
images cannot establish temporal continuity. Investigate an original sequence
with timestamps, starting with KITTI raw data and its official AWS registry.
Record exact terms and access before downloading. Use only one RGB camera as
inference input; sensor references remain evaluation-only. Keep the selected
sequence in development and reserve other sequences for held-out evaluation.

## Decisions and limits

PyAV is selected for direct PTS access. Use the existing YOLO11n weights as the
initial candidate instead of changing model families during environment work.
Explicit device selection and fixed inference resolution make runs comparable.
No model/clip download occurs at import or inside CPU tests. Library, model and
dataset licenses remain separate; the owner still selects the source license.
Numerical TTC/range, path overlap, collision warnings and deployment await their
own later gates.
