# Repository setup status

Scope: all foundation setup steps, with feature implementation excluded by the
owner on 2026-10-04. Work is published through
[setup PR #1](https://github.com/izar-hasson/monocular-collision-warning/pull/1).
Phase 0 remains open because protection enforcement has not passed its gate.

## Prepared and verified

- Installable `src/` package and help/version CLI; five real CPU smoke cases.
- Python 3.12, uv 0.12.23 and committed lock; Ruff, mypy, pytest, pre-commit,
  editor settings, asset/cache ignore rules and documented Makefile commands.
- Private GitHub repository, `main`, review branch, local remote/tracking refs and
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

## External setup blocker

[Issue #3](https://github.com/izar-hasson/monocular-collision-warning/issues/3)
tracks the remaining protection work. Owner login verified on 2026-10-05:

- Branch metadata: `main` is unprotected; status-check enforcement is off and
  required contexts are empty.
- The rulesets API returned HTTP 403 with the message
  `Upgrade to GitHub Pro or make this repository public to enable this feature.`
- Owner GitHub CLI authentication as `izar-hasson` is complete and the repository
  reports administration access. The connector's separate permission limit is
  unchanged, but it no longer prevents owner CLI administration.
- An owner-authenticated protection GET and an attempt to apply the reviewed
  protection payload by PUT both returned HTTP 403 with the Pro/public-repository
  requirement. No protection setting was applied or weakened.
- The research description and repository topics were applied and read back.
  Automatic deletion of merged PR branches is enabled. Default branch remains
  `main`; the repository remains private.

The [GitHub protected-branch documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
states that private-repository protection requires an eligible paid plan.
Owner administration access is ready. Keep this repository private until the
owner explicitly approves publication, or enable an eligible plan for private
protection. The owner was asked to choose; login completion alone is not approval
to change privacy or purchase a subscription.

Once those prerequisites are available:

1. Inspect existing settings and preserve stronger rules. Apply the reviewed
   [main protection payload](../.github/main-protection.json), or equivalent
   settings: PR required, **CPU checks** required, branches up to date,
   administrator enforcement, force pushes/deletion disabled. External approvals
   may remain optional for a solo maintainer.
2. Repeat the deliberate failure/restoration PR under enforced protection and
   record that the required check blocks merging while failed and clears when
   passing. Close that validation PR without merging.
3. Require the setup PR's latest hosted check to pass, merge through the PR, and
   record the final `main` commit/checks. A foundation tag is optional and must
   wait until all gates pass.

No gate is waived by publishing this checklist. The actual commands and validation
procedure are in [github-governance.md](github-governance.md).

## Decisions kept explicit

Public source licensing is deferred to the owner's release decision; the exact
tool/library/model/data review boundaries are in
[third-party-licenses.md](third-party-licenses.md). No models or datasets have
been selected, no CUDA migration has occurred, and no feature implementation is
authorized. After setup is finished, stop until the owner requests feature work.
