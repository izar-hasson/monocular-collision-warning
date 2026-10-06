# Detection and tracking implementation plan

Owner authorization: 2026-10-05. Phase 0 is complete. This request starts
Phase 1 (video/detection), followed by Phase 2 (tracking); phases 3–7 remain
outside this change. No phase is complete merely because its code exists.

Update 2026-10-06: the owner requested a runnable detection test script. The
existing-environment script passed real-model CPU image/12-frame KITTI smoke
checks and saves annotated frames. The owner subsequently authorized PyAV
installation and shared video-reader integration. The locked `video` extra,
generated-video timestamp tests and a real-model CPU run on a lossless video
encoded from those 12 KITTI frames passed. A locked GPU environment and full
recorded-video CLI acceptance remain pending; Phase 1 stays open and Phase 2 has
not started. See [detection.md](detection.md).

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
