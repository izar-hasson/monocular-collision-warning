# Contributing

Work on one bounded task from [HANDOFF.md](HANDOFF.md). Each change needs a clear
purpose, explicit scope, and a meaningful acceptance check. Introduce contracts
and interfaces with real consumers; keep numerical estimation/risk logic separate
from video, model, visualization, and GPU adapters.

## Setup and checks

Use Python 3.12 and uv 0.12.23. Follow [development.md](docs/development.md) and
preserve the separate [GPU baseline](docs/environment-baseline.md).

```bash
uv sync --locked
make hooks
make check
uv run --locked pre-commit run --all-files
```

Use `uv run --locked` for individual commands. Review dependency edits with their
generated `uv.lock` changes; never edit the lockfile manually. New Python files
must be staged for Git-aware hooks to see them. Local hook results do not replace
the required hosted status check.

## Branches and pull requests

Create a branch from current `main`, using `chore/`, `feat/`, `fix/`, or `docs/`
plus a short purpose, such as `chore/cpu-ci`. Keep each PR focused on one roadmap
task. Use the PR template to describe the problem, final behavior, commands and
results, documentation, reproducibility, failure modes, and licensing changes.

The required GitHub status check is **CPU checks** from the **CPU CI** workflow.
Require it to pass before merging, with the branch up to date. Use a PR for
changes to `main`; block force pushes and branch deletion. External reviewer
approval may be optional for a solo maintainer, but checks remain required.
Never bypass or quietly disable a failed check. The enforcement configuration and
validation procedure are in [github-governance.md](docs/github-governance.md).

## Test and documentation expectations

CPU tests use deterministic synthetic inputs and need no models, CUDA, or network.
Lightweight integration tests may run by default. GPU, slow/video, and benchmark
tests are opt-in. Use analytic known answers for geometry/TTC, and separate
recorded-video demonstration from ground-truth evaluation. A test should fail for
a plausible bug; no placeholder passing tests or unexpected core skips.

Update the relevant README, contract documentation, ADR, and handoff state when a
task changes them. State checks not executed and avoid invented outcomes, model
confidence relabeled as collision probability, or missing evidence called safe.

Keep raw data, model weights, private media, secrets, and generated outputs out of
Git. Model, library, and dataset licenses are separate decisions; record exact
versions, sources, checksums, rights, and known limitations before adoption or
redistribution. Public license selection remains pending.
