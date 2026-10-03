# CPU CI and GitHub governance

## Current state

PR 0C provides a local workflow, PR template, contribution guide, and reviewable
branch-protection payload. At preparation time this checkout has no GitHub remote,
the connected account lists no accessible repositories, and local GitHub CLI
authentication is unavailable. Hosted CI, branch protection, and the failing-PR
gate have not been exercised. PR 0C remains incomplete until that evidence exists.

Local verification on 2026-10-04 passed actionlint 1.7.12, workflow configuration
consistency checks, and all workflow shell commands. Those commands also passed
in a clean local clone of the committed PR 0B foundation with a new CPU environment:
five tests, lint/format/types, and sdist/wheel import/CLI smoke. Adding a deliberate
failing test only to that temporary clone returned pytest exit 1; restoring it
returned five passing tests. The lockfile hash stayed unchanged. These results
verify the run commands locally, not the GitHub setup actions or merge enforcement.

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

## Configure main protection after connecting GitHub

First select the intended repository and inspect its current contents/settings.
Publish the local history without overwriting unrelated work. Ensure the workflow
runs and its **CPU checks** check is registered before choosing the required check.

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
