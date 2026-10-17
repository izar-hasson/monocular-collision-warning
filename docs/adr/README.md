# Architecture decision records

Record consequential choices with a numbered file containing date, status,
context, decision, alternatives/trade-offs and consequences. Use `proposed`,
`accepted` or `superseded`; link the replacement when superseding an accepted
decision. Preserve the reason for an earlier choice rather than deleting its
history. Routine edits do not need an ADR.

- [0001: Repository foundation](0001-repository-foundation.md) — accepted;
  packaging, locked CPU checks, CI boundaries and deferred GPU dependencies.
- [0002: Timestamped detection](0002-video-detection.md) — accepted;
  source time, detector isolation, provenance and optional inference setup.
- [0003: CPU ByteTrack backend](0003-tracking-backend.md) — accepted for Phase 2
  milestone 1; pinned independent backend and characterized integration limits.
- [0004: Tracking lifecycle](0004-tracking-lifecycle.md) — accepted for milestone 2;
  measured histories, continuity segments, reset epochs and shared preview use.
