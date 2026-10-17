# ADR-0004: Measured tracks, reset epochs and continuity segments

Status: accepted for Phase 2 milestone 2, 2026-10-17.

## Context

[ADR-0003](0003-tracking-backend.md) selected and characterized CPU ByteTrack.
The owner subsequently requested video previews, then explicitly authorized the
domain adapter, lifecycle and bounded histories. The preview's private association
implementation would duplicate the tracker boundary. Later numerical code needs
safe histories independent of YOLO, decoded pixels and backend predictions.

## Decision

Introduce immutable tracking domain values and a `Tracker` protocol with
`update(FrameInfo, Sequence[Detection])` and `reset()`. Implement `ByteTrackAdapter`
with lazy optional imports and make the preview consume it. Return every original
observation in input order, including unassigned/below-floor observations, using
attached backend indices to recover original measurements.

Partition by class. Namespace identities by adapter UUID, reset epoch and
class/backend ID, with source recorded separately. Reset on source, resolution,
skipped-index and configured source-time discontinuities; reject invalid ordering
within a source before mutation. Explicit reset returns ended identities. Partial
backend failure raises and invalidates its epoch.

Maintain observed/lost tracks and explicit end events. Expose scores, observation
counts, age and time since observation as evidence, not physical probabilities.
Histories start when a confirmed ID becomes available; tentative observations
are not backfilled.

Retain original detections in the current continuity segment, bounded by count
(default 30) and source age (default 2 seconds). Prune on empty frames and expire
inactive identities. Never append predictions. Reacquisition increments the
segment and clears old history, preventing accidental numerical joins across
dropouts. Old immutable snapshots remain stable as internal buffers advance.

Keep JSONL compact: persist each frame's observations once with IDs/segments,
plus retention summaries and end/reset events. In-memory clients receive full
bounded history tuples.

## Consequences

Detection behavior and dependency pins are unchanged. The preview keeps its
command/options and gains history/gap limits. Historical preview evidence retains
its earlier schema/hashes; new output records epoch-aware IDs and lifecycle.

These boundaries fragment history on class changes, skipped frames and
reacquisition. That sacrifices some coverage to expose gaps; it does not detect
every backend identity switch. History bounds do not limit memory held by
downstream clients retaining old snapshots.

This milestone does not implement numerical estimators, full detection/tracking
orchestration or Phase 2 accuracy/performance acceptance. See the
[tracking guide](../tracking.md) for the contract, commands and limitations.

Subsequent Phase 2 finalization adds full orchestration through the shared pipeline
and [recorded-video acceptance](../phase2-acceptance.md). The history and identity
decisions above remain unchanged; numerical estimators are still deferred.
