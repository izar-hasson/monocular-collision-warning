# ADR-0001: Repository foundation

- Date: 2026-10-04
- Status: accepted; PR 0A/0B implemented; PR 0C hosted CI verified, protection/enforcement pending

## Context

The project needs an installable, verifiable Python foundation before perception
features. A previously working CUDA/YOLO environment exists separately and must
be preserved. This execution environment has Python 3.12.3; the foundation can
be verified without GPU hardware or model weights.

## Decision

Use Python 3.12 as the initial development/test target, declare Python >=3.12,
and use a `src/collision_warning` package with setuptools as the standard build
backend. Expose `collision-warning` through package metadata. Read the CLI version
from installed distribution metadata to keep one version source.

Use `uv` to manage project environments and `pyproject.toml` for dependency
definitions. PR 0A used explicit `uv venv` / `uv pip install` commands for its
installation gate. PR 0B generates `uv.lock` for version control, adopts locked
project sync/run commands, and adds Ruff, targeted mypy, and local pre-commit hooks
that invoke those same tools. Pin uv to 0.12.23 and the isolated build backend to
setuptools 84.0.0; review tooling updates explicitly.

Test installed imports with an isolated Python process and the actual console
script from a temporary working directory, using pytest importlib mode. Keep
the foundation free of runtime ML dependencies.

PR 0C defines deterministic CPU CI with the required check name `CPU checks`,
full verified action SHA pins, and a build/isolated wheel smoke. Hosted passing,
intentional failing, and recovered passing runs are recorded in
[GitHub governance](../github-governance.md). Branch protection and required-check
merge enforcement remain pending. Later GPU/model/video/benchmark tests will be
explicitly opt-in, and CUDA dependencies will be introduced as optional extras
only when Phase 1 needs them. The historical GPU baseline is not assumed to have
been recreated here.

## Alternatives and trade-offs

A flat layout or root script would be faster to sketch but can hide broken
installation behind source-directory imports. A `src` layout plus real console
tests exposes packaging errors. Setuptools supplies conventional package
discovery without adding a custom build mechanism.

Adding GPU inference now would enlarge installation and validation requirements
without helping the PR 0A gate. Keeping the base package dependency-free makes
CPU verification straightforward. The provisional unlocked PR 0A setup was
replaced by locked setup in PR 0B. Local system-language hooks share the project's
locked tools instead of resolving a second independent set of hook dependencies.

## Consequences and deferred decisions

Consumers must install the package before using it. CPU developer dependencies
are locked; this does not guarantee bitwise GPU reproducibility across hardware
or drivers. Passing hosted CI verifies the package/tooling foundation; video
processing and warning performance remain unimplemented and unvalidated.
Only Python 3.12 is initially verified; the lower-bound metadata is not evidence
that every later Python version was tested.

Defer detector weights/version, tracking implementation, calibration, smoothing,
warning thresholds, external datasets, and optimization to their roadmap gates.
Do not add depth networks, ROS2, cloud services, Docker, DVC/MLflow, or an empty
plugin architecture without measured need. Public license selection remains
pending the [license audit](../third-party-licenses.md).

## Upstream guidance consulted

- [PyPA: pyproject metadata and console scripts](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [uv: explicit virtual environments](https://docs.astral.sh/uv/pip/environments/)
- [pytest: installed-package testing and import modes](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
