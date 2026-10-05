# Monocular Collision Warning

An offline research prototype for estimating collision-related motion from a
forward-facing, timestamped RGB dashcam stream. The planned pipeline detects and
tracks road users, estimates image-expansion TTC and calibrated ground-plane
geometry, then assesses relative paths and emits inspectable warnings.

Inference will use monocular RGB only. External sensors may supply evaluation
references. Arbitrary uncalibrated images do not establish metric distance, and
TTC alone does not establish collision-path overlap. Missing evidence must remain
unknown.

**Research use only.** This is not a certified automotive safety system, a
substitute for driver attention, or a system permitted to control a vehicle.

## Current state

Phase 0 repository setup is prepared in
[PR #1](https://github.com/izar-hasson/monocular-collision-warning/pull/1): installable
package, help/version CLI, locked CPU checks, hosted CI, contribution/issue
templates, data/model conventions, license inventory, and evaluation plan.
Hosted CPU CI passed; a controlled PR verified failure and recovery. The remaining
gate is branch protection and required-check merge enforcement, blocked by this
private repository's current GitHub plan. Owner administration login is now verified.
See the [setup checklist](docs/repository-setup.md).

Feature implementation is paused at the owner's request. Video detection,
tracking, TTC, geometry, and warnings are unimplemented. No performance or
predictive-accuracy results are claimed.

Python 3.12 is the initial development target. The owner's earlier RTX 5070 Ti
YOLO/CUDA checks are recorded in [HANDOFF.md](HANDOFF.md); they are historical
development evidence, not results from this package.

## Quickstart (Ubuntu / WSL)

Install `uv` **0.12.23** using the [official instructions](https://docs.astral.sh/uv/getting-started/installation/).
With access to this private repository, clone using your usual GitHub
authentication. While the setup PR is open, select its branch:

```bash
git clone https://github.com/izar-hasson/monocular-collision-warning.git
cd monocular-collision-warning
git switch chore/cpu-ci
```

After the setup PR is merged, use `main`. From the repository root with Python
3.12 installed:

```bash
uv sync --locked
uv run --locked collision-warning --help
uv run --locked collision-warning --version
make check
```

`make check` runs Ruff lint, formatting verification, targeted mypy, and CPU pytest.
The commands and optional pre-commit setup are documented in
[development.md](docs/development.md). Requirements live in `pyproject.toml`;
`uv.lock` records their resolution. Use locked commands for routine work and
review intentional dependency updates together with their lockfile changes.

The base package has no runtime dependencies or model downloads. It does not
recreate CUDA; preserve the separate working GPU environment. Its verified versions
and migration rules are recorded in the [environment baseline](docs/environment-baseline.md).
See [CONTRIBUTING.md](CONTRIBUTING.md) for PR conventions and
[GitHub governance](docs/github-governance.md) for the required `CPU checks` gate.

## Architecture and roadmap

See [architecture and scientific contracts](docs/architecture.md),
[ADR-0001](docs/adr/0001-repository-foundation.md), and the detailed
[handoff](HANDOFF.md). The [evaluation plan](docs/evaluation-plan.md),
[data conventions](data/README.md), [model conventions](models/README.md), and
[resource ledger](docs/resources.md) define evidence required before adoption.

| Phase | Deliverable |
| --- | --- |
| 0 | Package foundation → locked local checks → CPU CI/governance → provenance audit |
| 1–2 | Timestamp-preserving video input, detector adapter, then tracking/history |
| 3–4 | Validity-gated looming TTC, then calibrated road geometry |
| 5–6 | Relative motion/path overlap, then uncertainty-aware warning policy |
| 7 | Held-out evaluation, stage timing, and measured optimization |

Each step must pass its acceptance gate before the next begins. Finish repository
protection and merge enforcement first; feature work needs a new owner request.
The [Phase 1 issue](https://github.com/izar-hasson/monocular-collision-warning/issues/4)
is planning only. GPU dependencies arrive with Phase 1.

## Licensing

A public repository license has not been selected. See
[third-party license audit notes](docs/third-party-licenses.md) for the separate
library, model, and dataset review gates.
