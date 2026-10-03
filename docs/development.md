# Development workflow

## Locked CPU setup

Use Ubuntu/WSL, Python 3.12, and uv 0.12.23. Keep the project under the Linux
filesystem and work from the repository root. `.python-version` selects Python
3.12; `pyproject.toml` enforces the uv version used to generate the lockfile.

```bash
uv sync --locked
uv run --locked collision-warning --help
uv run --locked collision-warning --version
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest -q
```

`make setup` runs the sync command. `make check` runs lint, format check, type
check, and tests sequentially, propagating failures. Its individual targets are
`lint`, `format-check`, `typecheck`, and `test`. Mypy currently checks the real
`src/collision_warning` package; expand the target as domain/core code appears.

The dev dependency group is installed by default. The build backend version is
also pinned in `pyproject.toml`, since build-isolation dependencies are separate
from the project lock. Do not edit `uv.lock` manually or make unmanaged pip changes
inside this project environment.

For an intentional dependency change, edit `pyproject.toml` or use `uv add --dev`,
then run `uv lock`, `uv sync --locked`, and `make check`. Review and commit both
metadata and lock changes. Use `uv lock --check` to verify consistency. A stale
lock must fail instead of being silently rewritten. Changing the uv pin is a
reviewed tooling update.

## Tests and hooks

Default pytest uses importlib mode, strict configuration/markers, and excludes
`gpu`, `slow`, and `benchmark`. Small CPU `integration` tests remain eligible.
The current suite contains five packaging/CLI smoke cases; no GPU, video, or
benchmark tests have been implemented. Do not add passing placeholder tests.

When real tests exist, opt in with `uv run --locked pytest -m gpu`, `-m slow`, or
`-m benchmark`. These explicit selectors replace the default marker selection.
GPU tests will require the future GPU extra and locally verified weights;
the current CPU environment cannot satisfy them.

```bash
make hooks
uv run --locked pre-commit run --all-files
```

Hooks run the locked local tools, with no independent hook dependencies. They
check lock consistency, lint, formatting, and package types. Python hooks see
Git-tracked files, so stage new files before checking them; `make check` covers
the working tree directly. Hooks do not auto-fix files. Apply an intentional
formatting edit with `uv run --locked ruff format .`, then rerun checks.
The PR 0C workflow is checked in, but hosted execution and protection are pending
repository access. See [GitHub governance](github-governance.md) and
[CONTRIBUTING.md](../CONTRIBUTING.md); passing local hooks is not hosted-CI evidence.

## Existing CUDA environment

Follow [the baseline and migration rules](environment-baseline.md). The sibling
demo environment is separate from this project's `.venv`. Do not run `uv sync`
against it or overwrite it while testing CPU setup. Phase 1 must document and
verify an optional CUDA installation before any migration.

Private environment captures belong in gitignored `local-baselines/`. Raw media,
weights, outputs, caches, and environment files are ignored. Later synthetic
fixtures may be committed under `tests/fixtures`; external assets need provenance
and redistribution review before any Git-ignore exception.

## Restricted execution environments

For a sandbox with a read-only user cache, choose a writable cache with
`UV_CACHE_DIR=/tmp/mono-collision-uv-cache`. If uv is available only as a temporary
executable, use `make UV=/path/to/uv check`. These are local execution overrides;
no machine-specific paths belong in tracked configuration.

## Upstream references

- [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
- [Local pre-commit hooks](https://pre-commit.com/#repository-local-hooks)
- [pytest marker selection](https://docs.pytest.org/en/stable/example/markers.html)
