# CPU CI and GitHub governance

## Current state

The private repository is
[izar-hasson/monocular-collision-warning](https://github.com/izar-hasson/monocular-collision-warning).
[PR #1](https://github.com/izar-hasson/monocular-collision-warning/pull/1) contains
PR 0C's workflow, PR template, contribution guide, and proposed protection payload.
Hosted CI is verified. Owner-authenticated inspection on 2026-10-05 reported
`main` as unprotected with no required contexts. PR 0C remains open until protection
and required-check merge enforcement are verified. Owner GitHub CLI login is now
confirmed with administration access; the connector itself still lacks that
permission. The current blocker is the private repository's GitHub plan.

The owner expanded the scope to all repository setup on 2026-10-04 while excluding
feature implementation. The PR also prepares provenance/evaluation documentation
and templates. The remaining gate is tracked in
[issue #3](https://github.com/izar-hasson/monocular-collision-warning/issues/3).
GitHub's rulesets endpoint returned HTTP 403 requiring GitHub Pro or a public
repository. Its branch-protection endpoint separately returned HTTP 403 because
the integration lacks administration access. On 2026-10-05, owner CLI login
resolved the administration-access blocker, but both protection GET and the
reviewed protection PUT still returned HTTP 403 requiring GitHub Pro or a public
repository. The repository remains private; no protection gate was waived.
See [repository-setup.md](repository-setup.md) for the complete checklist.

## Hosted evidence — 2026-10-04

| Check | Commit | Hosted run / result |
| --- | --- | --- |
| Initial PR #1 | `fbe70b44ea6d4847f362cc59010077300fb58642` | [37157161465](https://github.com/izar-hasson/monocular-collision-warning/actions/runs/37157161465): CPU checks passed all steps, five tests and isolated wheel smoke |
| Deliberately incorrect CLI help assertion | `fd2c6dbd1d858517d3377e61c79a70ec538420ce` | [37157365906](https://github.com/izar-hasson/monocular-collision-warning/actions/runs/37157365906): lint/format/types passed; pytest failed with two failed, three passed and exit 1; wheel step skipped |
| Original assertion restored in a new commit | `c75f0ab2e257ff2c9e9cec24d2672007365d56a9` | [37157690963](https://github.com/izar-hasson/monocular-collision-warning/actions/runs/37157690963): CPU checks passed all steps |

The disposable [PR #2](https://github.com/izar-hasson/monocular-collision-warning/pull/2)
was closed without merging. While `main` was unprotected, its merge state was
`unstable` on the failed commit and `clean` after recovery. This proves hosted
failure/recovery, but does not prove required-check enforcement. Once protection
is enabled, repeat the negative check and inspect merge blocking before closing
the PR 0C gate. No failing check was waived.

Local verification passed actionlint 1.7.12 and every workflow shell command in a
clean local clone with a new CPU environment. The lockfile hash stayed unchanged.
Hosted runs additionally verify checkout, Python/uv setup actions, and the complete
CPU job on Ubuntu 24.04.

## Workflow contract

[CPU CI](../.github/workflows/ci.yml) runs on every push and pull request without
path filters. Its single required check is **CPU checks**. Ubuntu 24.04 and Python
3.12 run locked CPU developer setup, Ruff lint/format checks, targeted mypy, and
default pytest. The final step builds an sdist/wheel and verifies the wheel's
isolated import and console command in a separate environment outside the source
directory. It performs no model downloads or GPU checks.

The workflow token has only `contents: read`; checkout does not persist its
credentials. It does not execute `pull_request_target` with elevated access,
require custom secrets, or reuse developer machine paths. Step failures fail the
job; there is no `continue-on-error`. Concurrent runs for the same branch/PR
cancel obsolete work. Cache optimization is deferred.

## Action pin provenance and update policy

Pins were verified against official release pages and the corresponding action
definitions on 2026-10-04.

| Action | Release | Immutable commit |
| --- | --- | --- |
| actions/checkout | [v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1) | [3d3c42e5aac5ba805825da76410c181273ba90b1](https://github.com/actions/checkout/commit/3d3c42e5aac5ba805825da76410c181273ba90b1) |
| actions/setup-python | [v7.0.0](https://github.com/actions/setup-python/releases/tag/v7.0.0) | [5fda3b95a4ea91299a34e894583c3862153e4b97](https://github.com/actions/setup-python/commit/5fda3b95a4ea91299a34e894583c3862153e4b97) |
| astral-sh/setup-uv | [v10.2.0](https://github.com/astral-sh/setup-uv/releases/tag/v10.2.0) | [c18668ad3cf93ea998bef934396af7bb5c839dc7](https://github.com/astral-sh/setup-uv/commit/c18668ad3cf93ea998bef934396af7bb5c839dc7) |

Update an action in a scoped PR: verify the upstream release-to-commit mapping,
read its action inputs/runtime and release changes, update both the SHA and version
comment, rerun workflow lint and local checks, then require hosted CI. Keep full
SHAs; do not replace them with moving tags. Python and uv versions come from the
existing `.python-version` and `pyproject.toml` settings.

## Configure main protection

The **CPU checks** job is now registered. In
[branch settings](https://github.com/izar-hasson/monocular-collision-warning/settings/branches),
create protection for `main`: require a PR, require **CPU checks** with branches
up to date, and enforce the rules for administrators. Keep force pushes and
deletion disabled. External approvals may remain optional for this solo project.
Inspect existing settings first and preserve any stronger rules.

[main-protection.json](../.github/main-protection.json) requests an up-to-date
required check, PR-based changes, zero mandatory external approvals for the solo
maintainer, enforcement for administrators, and blocked force pushes/deletion.
Read existing settings first; do not overwrite stronger existing protections with
this foundation payload. Apply the appropriate equivalent through repository
settings or, with an authenticated GitHub CLI and administration rights:

```bash
gh api --method PUT repos/OWNER/REPO/branches/main/protection \
  --input .github/main-protection.json
gh api repos/OWNER/REPO/branches/main/protection
```

Substitute the selected owner/repository and inspect the returned configuration.
The checked-in JSON does not enforce anything until applied to GitHub. If the
account/repository cannot enable protection, record the actual rejection and keep
the gate open; do not describe `main` as protected.

## Prove the hosted gate

1. Publish the workflow and open a focused test PR. Observe the named CPU job.
2. On that PR branch, deliberately break a meaningful smoke assertion. Verify
   the hosted **CPU checks** job fails and the PR merge state is blocked by the
   required check. This controlled negative check may require an explicit hook
   bypass on the disposable validation branch; keep the failed result recorded.
3. Restore the test in a new commit. Verify the same hosted job passes and the
   failed required-check block is cleared. Review any other remaining merge
   requirements separately; a draft PR can still be unmergeable.
4. Record repository/PR URLs, failing/passing commit SHAs and run URLs, and the
   inspected protection state in the handoff. Close the validation PR without
   merging the deliberately broken test. Never merge it or waive checks.

Local workflow lint, CPU runs, and intentional local failures help review the
configuration, but do not establish hosted status-check or merge enforcement.

## Official guidance

- [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use)
- [Protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Branch-protection API](https://docs.github.com/en/rest/branches/branch-protection#update-branch-protection)
