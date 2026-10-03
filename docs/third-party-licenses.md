# Third-party license audit notes

Date: 2026-10-04. Status: initial review ledger; public license selection pending.
The foundation has no runtime third-party dependencies, bundled model weights,
or dataset/media assets. PR 0B records exact tool versions below and transitive
developer dependencies in `uv.lock`; upstream license review remains a PR 0D
and public-release gate.

| Category | Component | State / next action |
| --- | --- | --- |
| Library/tool | setuptools 84.0.0, uv 0.12.23, pytest 9.1.1 | Pinned build backend and locked tooling; upstream license verification pending |
| Library/tool | Ruff 0.16.10, mypy 2.4.0, pre-commit 4.6.2 | Locked developer tools; upstream and transitive license verification pending |
| Library | Ultralytics, PyTorch, OpenCV, tracker implementation | Future integrations; audit exact selected packages and transitive terms before adoption |
| Model | Detector pretrained weights | Not selected or redistributed; record exact upstream source, version, SHA-256, and separate weight terms in Phase 1 |
| Dataset/media | Dashcam clips and annotations | Not selected; confirm access, use, redistribution, provenance, splits, and privacy requirements before acquisition/use |
| Repository | Project source license | Not selected; no LICENSE boilerplate or SPDX assertion has been added |

Before public release or redistribution, consult exact official license files and
record the review date, versions, permitted uses, attribution requirements, and
unresolved questions. In particular, review Ultralytics' published terms and the
chosen model/data terms before integrating them. A catalog link or installed
library does not establish rights for associated weights or footage.

Keep library, model, and dataset decisions separate. Leave candidates deferred
when rights or provenance remain unclear. See [HANDOFF.md](../HANDOFF.md),
sections 5.3 and 8, for the review gates. These notes record pending engineering
decisions and do not constitute a completed legal assessment.
