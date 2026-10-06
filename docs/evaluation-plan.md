# Evaluation plan

Status: detection/tracking implementation authorized 2026-10-05. Phase 1 adds
video/detection contracts and run measurements; acceptance remains evidence-gated.
Tracking, TTC, geometry and warnings follow their respective roadmap gates. No
predictive-accuracy result is claimed. This plan specifies evidence to collect
as each roadmap component lands.

## Inputs and splits

Start with deterministic synthetic unit cases having analytic expected results.
Use licensed, sequence-separated development clips for integration and a frozen
held-out set for final evaluation. Record the exact asset/annotation versions,
checksums, permitted uses, source timestamps and reference alignment using
[data conventions](../data/README.md) and
[clip-manifest.v1.json](templates/clip-manifest.v1.json).

The manifest is a versioned blank template, not a collected dataset. Missing
rights, labels, calibration or timestamps must remain explicit. Do not evaluate
TTC/range against numbers inferred by the same estimator being evaluated.

## Scenario matrix

These are proposed cases; no listed case implies footage or reference labels
already exist. Record positive, negative and unavailable outcomes independently.

| Proposed scenario | Expected evidence/behavior to test later | Reference required |
| --- | --- | --- |
| Approaching target in same lane | Valid approach estimate if assumptions hold; evaluate path overlap separately | Time-aligned motion/TTC and event labels for numerical/event claims |
| Adjacent lane, similar image expansion | Expansion alone must not trigger a collision-path claim | Lane/path/event reference |
| No expansion, stationary image scale or receding object | Looming estimate unavailable; no invented zero or infinity | Synthetic scale/time history initially |
| Crossing pedestrian / cut-in | Temporal association and changing path evidence; confidence is not collision probability | Reviewed track/path/event labels |
| Acceleration / braking | Lag, derivative assumptions and warning lead time | Independently derived reference motion/events |
| Occlusion, dropout, identity switch | Reset or invalidate derived motion; expose unavailable periods | Synthetic histories plus reviewed track IDs |
| Rotation, turns, camera shake, grades | Flag invalid assumptions; image size change is not assumed depth closure | Reviewed scene labels and calibration/motion reference if making metric claims |
| Empty scene / benign traffic | Negative controls for warning frequency | Reviewed no-warning exposure/events |
| Night, rain or glare | Report a separate breakdown only if licensed clips cover it | Actual scene/visibility labels; regional weather is insufficient |

## Metrics and denominators

Freeze definitions, matching tolerances and thresholds on development data before
opening held-out results. Report unavailable coverage and annotation uncertainty
alongside errors; exclude invalid measurements explicitly rather than treating
them as safe or perfect predictions.

| Layer | Planned metrics and reporting conditions |
| --- | --- |
| Detection | Per-class precision/recall or AP with declared box-matching thresholds and label coverage |
| Tracking | ID switches/continuity; choose a documented tracking metric only when reference IDs support it |
| Looming TTC | Error in seconds against independent TTC, error breakdown by validity/assumption, available/total eligible observations |
| Ground geometry | Lateral/longitudinal error in meters by distance and scene, valid coverage, sensitivity to reviewed calibration |
| Warning events | Matched/missed reference events, false warnings per reviewed hour (or another stated exposure), lead time, event duration, transitions/flicker and unknown rate |
| Runtime | Cold start separately; warmed stage/end-to-end latency p50/p95, processed FPS, input FPS/frame drops and peak memory under declared conditions |

For warnings, define the reference event onset/end and the allowed matching window
before scoring. Report matched, missed and unmatched predicted event counts;
declare how multiple warnings for one event are handled. Lead time needs an
independent reference onset. Frame counts are not distinct event counts. Always
state exposure/sample size and give per-scenario breakdowns, including failures.

## Timing and comparisons

Record hardware, OS/driver, Python/package versions, model checksum, resolution,
precision, batch size, device, source checksums and exact configuration. Declare
warm-up and repeat counts. Include decoding/output in end-to-end timing; report
separate stages where useful. Future CUDA measurements must account for
asynchronous execution. Source presentation time drives motion; processing wall
time measures latency. Compare implementations on the same clips/conditions.

Save a reviewed configuration and
[run-manifest.v1.json](templates/run-manifest.v1.json) beside local results under
gitignored `runs/<run-id>/`. Null fields in the template mean unrecorded, not
zero. Replace them with actual evidence before describing a run as measured;
retain failed runs and limitations. Use a new manifest schema version for changed
field meaning. DVC/MLflow and an automated harness remain deferred until needed.

## Before feature work

Repository governance and Phase 0's setup gate are complete. The original
[Phase 1 issue](https://github.com/izar-hasson/monocular-collision-warning/issues/4)
defines the first bounded implementation proposal and a planned demo command;
the owner's new request authorizes detection and tracking. Numerical and warning work
remain later gates in [HANDOFF.md](../HANDOFF.md).
