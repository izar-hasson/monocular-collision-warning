# Repository setup status

Scope: all foundation setup steps, with feature implementation excluded by the
owner on 2026-10-04. Work is published through
[setup PR #1](https://github.com/izar-hasson/monocular-collision-warning/pull/1).
Phase 0 is complete as of 2026-10-05. PR #1 merged at `4580e6ad6b275298e481570c1bbc42a5d92548c2`;
[CI on merged main](https://github.com/izar-hasson/monocular-collision-warning/actions/runs/37318348053) passed all steps. Feature work needs a new
owner instruction.

## Completed and verified

- Installable `src/` package and help/version CLI; five real CPU smoke cases.
- Python 3.12, uv 0.12.23 and committed lock; Ruff, mypy, pytest, pre-commit,
  editor settings, asset/cache ignore rules and documented Makefile commands.
- Public GitHub repository, default `main`, PR workflow, local remote/tracking refs and
  preserved original local history.
- Hosted CPU CI with full verified action pins, read-only token permissions and
  isolated wheel verification. Controlled hosted failure and recovery recorded in
  [GitHub governance](github-governance.md); validation PR closed without merging.
- PR/issue templates, contribution guide and CODEOWNERS for the solo maintainer.
- Data/model provenance conventions, evaluation plan, versioned blank clip/run
  manifests, research ledger, ADR convention and exact tool-license inventory.
- A [future Phase 1 issue](https://github.com/izar-hasson/monocular-collision-warning/issues/4)
  with inputs, outputs, acceptance cases and an explicitly unimplemented demo
  command. It is a planning record, not an instruction to implement it.

Fresh local-clone validation passed locked setup, CLI help/version, lint/format,
types, all five tests, pre-commit, sdist/wheel build, and isolated wheel smoke with
new environments. The clone remained clean and `uv.lock` unchanged. Packages
came from an existing cache offline; this was not a credentialed network clone.
Relative file links and JSON/YAML configurations were checked. Tracked files and
historical blobs contained no large binaries or known secret-pattern matches
(a heuristic check). Evidence is recorded in the handoff and local audit records.

## Protection and final merge gate

The owner completed CLI authentication and made the repository public on
2026-10-05. This resolved the earlier owner-access and private-plan blockers.
The repository description and research topics were applied and read back;
automatic deletion of merged PR branches is enabled.

- [x] Inspected the previously unprotected main and empty rulesets, then applied
  [main-protection.json](../.github/main-protection.json) and read back the result.
- [x] Require PRs and up-to-date **CPU checks**; enforce administrators; disallow
  force pushes and deletion. External approvals are optional for the solo owner.
- [x] [Validation PR #5](https://github.com/izar-hasson/monocular-collision-warning/pull/5): real CLI assertion failed with two failed,
  three passed and exit 1; required check failed and merge state was `blocked`.
- [x] Restored the exact setup tree in a new commit; all CPU steps, five tests
  and wheel smoke passed; merge state became `clean`. Closed PR #5 without merging.
- [x] All setup-head check runs passed, including a rerun of the cancelled
  validation-branch push. Setup PR #1 was `clean` and merged with its expected
  head SHA, without bypassing protection.
- [x] Main push at `4580e6ad6b275298e481570c1bbc42a5d92548c2` passed [run 37318348053](https://github.com/izar-hasson/monocular-collision-warning/actions/runs/37318348053).

Exact failing/recovered SHAs and run URLs are in
[github-governance.md](github-governance.md). [Issue #3](https://github.com/izar-hasson/monocular-collision-warning/issues/3) records
the final setup and documentation verification. The optional foundation tag
is not required for these gates; no release has been published.

## Decisions kept explicit

Public source licensing is deferred to the owner's release decision; the exact
tool/library/model/data review boundaries are in
[third-party-licenses.md](third-party-licenses.md). No models or datasets have
been selected, no CUDA migration has occurred, and no feature implementation is
authorized. After setup is finished, stop until the owner requests feature work.
