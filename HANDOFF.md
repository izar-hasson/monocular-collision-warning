# Monocular Collision Warning — Engineering Handoff & Repository Blueprint

> **Status:** Phase 0 / PR 0A and PR 0B completed; PR 0C prepared and verified locally on 2026-10-04, with hosted CI/governance pending GitHub repository access. Phase 0 remains incomplete.
>
> **Prepared:** 2026-10-03; resource-library integration added 2026-10-03  
> **Audience:** Project owner, future collaborators, and AI coding agents.  
> **Working repository name:** `monocular-collision-warning` (rename before initialization if desired).  
> **Guiding principle:** Make every new component easy to implement, verify, replace, benchmark, and understand without rediscovering prior decisions.

## 0. Read this first — where we actually are

The project is an **offline/research prototype** of a real-time, monocular RGB dashcam collision-risk estimation and warning pipeline. It is **not** a certified automotive safety system, a substitute for driver attention, or a system permitted to control a vehicle.

**Confirmed so far by the owner:** Windows 11; WSL2/Ubuntu; RTX 5070 Ti; PyTorch `2.14.1+cu130`; CUDA reported as `13.0`; `torch.cuda.is_available() == True`; compute capability `(12, 0)`; a CUDA tensor multiplication succeeded; an Ultralytics YOLO bus/person image prediction produced annotated detections. These checks establish a working development baseline, **not** successful video tracking, distance estimation, TTC estimation, or validated warning performance. Record Python, Ubuntu, driver, `uv`, Ultralytics, OpenCV, and actual package versions during bootstrap; they have not all been verified.

**Decision already made:** use the hybrid modular architecture in §2, and build feature-by-feature using the gated roadmap in §4. **Immediate focus:** §5 Phase 0, the professional repository foundation. PR 0A's installation gate and PR 0B's repeatability gate have passed locally. Finish PR 0C's hosted CI and branch-protection evidence before advancing. Do **not** skip to another YOLO demo or add multiple feature implementations before the foundation passes its acceptance checks.

### PR 0C preparation record — 2026-10-04 (hosted gate pending)

- The owner authorized continuing with PR 0C. The checkout has no remote. The connected GitHub profile is accessible, but the connector lists no accessible repositories; `gh`, local CLI authentication, and exposed branch-protection mutation tools are unavailable. The repository destination was requested while local work continued. Do not assume a repository exists or publish to an unrelated destination.
- Added `.github/workflows/ci.yml`, the PR template, `.github/main-protection.json`, `CONTRIBUTING.md`, and `docs/github-governance.md`. Updated README, developer guide, ADR-0001, and this handoff. The required job name is `CPU checks`; token permissions are only `contents: read`, checkout credentials are not persisted, and the workflow uses ordinary push/PR events with no model/GPU requirements.
- Verified full action pins against official releases and action definitions: checkout v7.0.1, setup-python v7.0.0, and setup-uv v10.2.0. Recorded the SHA links and update policy in the governance document. Existing Python and uv version settings remain the source of truth.
- Downloaded actionlint 1.7.12 to a temporary tool directory, verified its official archive SHA-256, and successfully linted the workflow. Configuration checks confirmed workflow events, read-only permissions, full pins, and the matching protection check name.
- Executed every workflow shell step locally, then in a clean local clone of PR 0B commit `0bfb402` with a new CPU environment. Locked sync, lint, formatting, mypy, all five tests, and sdist/wheel build plus isolated import/CLI smoke passed. A deliberate test failure only in that clone made the workflow pytest command exit 1; restoring it returned five passing tests. The lockfile hash was unchanged. This is local evidence and does not validate the setup actions on hosted runners or prove GitHub merge blocking.
- The protection JSON is a reviewable proposed configuration, not applied policy. Hosted passing/failing PR runs and inspection of enforced `main` protection remain required. Repository creation/admin settings are not provided by the currently exposed connector capabilities; actual settings require appropriate repository access. Do not mark the PR 0C gate complete or advance to PR 0D on this local evidence alone.
- Local validation records are under gitignored `local-baselines/`; no media/model artifacts, public license, or CUDA migration were added. Next smallest task: identify/connect the intended repository, publish the reviewed foundation, verify hosted CI, apply/inspect protection, and exercise the failing/passing test PR.

### PR 0B implementation record — 2026-10-04 (historical)

- The owner authorized PR 0B and supplied a Git author identity, configured only in this repository. PR 0A was recorded as local commit `9c5abfd`; PR 0B has its own commit. No remote, hosted PR, CI, or branch rules have been configured.
- Added generated `uv.lock`, Python 3.12 selection, Ruff/pytest/mypy configuration, local pre-commit hooks, editor/line-ending settings, expanded asset/cache ignore rules, and thin Makefile targets. Added `docs/development.md` and `docs/environment-baseline.md`; updated README, ADR-0001, and the license ledger. No video/perception features were added.
- Pinned the uv tool to 0.12.23 and the isolated setuptools backend to 84.0.0. Locked developer tools are Ruff 0.16.10, mypy 2.4.0, pytest 9.1.1, and pre-commit 4.6.2, with transitive dependencies recorded in `uv.lock`. The lockfile was generated by uv and never edited manually.
- `uv sync --locked`, both CLI commands, `make check`, and `uv run --locked pre-commit run --all-files` passed twice without dependency churn. Each pytest run passed all five tests. SHA-256 checks confirmed the lockfile stayed unchanged. Hook configuration validated and the local Git hook was installed. Verification used a temporary uv executable and writable cache overrides because this sandbox's user cache is read-only; canonical tracked commands remain machine-independent.
- Temporary marker probes showed default pytest selected only CPU tests and deselected GPU/slow/benchmark cases; an explicit `-m gpu` selected the deliberately failing probe. These were configuration checks, not real GPU or benchmark tests. A stale-lock copy with changed project version failed `uv sync --locked` and retained its lockfile hash. No probe files were added to the project suite.
- Captured the existing demo's Python/package versions and pip freeze in gitignored `local-baselines/`. The public baseline note contains no user paths or machine IDs. Outside the sandbox, `nvidia-smi` reported RTX 5070 Ti / driver 616.64, and PyTorch CUDA availability, capability `(12, 0)`, and the 2×2 tensor multiplication passed. A post-check pip freeze matched the original snapshot exactly. No CUDA migration or YOLO prediction was performed.
- Baseline and verification records are local engineering artifacts, not model/data releases. Public license selection and upstream/transitive license audit remain pending. CPU setup does not recreate the full CUDA environment.
- Next: only PR 0C, CPU GitHub Actions and repository governance. Full Phase 0, literal clean-clone audit, hosted CI/branch checks, provenance audit, and Phase 1 remain pending.

### PR 0A implementation record — 2026-10-04 (historical)

- Initialized local Git on `main` in the existing `mono-collision-risk` folder. No remote, hosted PR, CI, or branch rules have been configured; changes are uncommitted.
- Renamed the supplied handoff to `HANDOFF.md`. Added README, `.gitignore`, setuptools `pyproject.toml`, the `src/collision_warning` package, help/version CLI, five CPU smoke cases, architecture documentation, ADR-0001, and initial third-party license audit notes. The distribution is `monocular-collision-warning`; the console command is `collision-warning`; its development version is `0.1.0.dev0`.
- Verified with Python 3.12.3, uv 0.12.23, and pytest 9.1.1. `uv venv --python python3.12 .venv` and `uv pip install --python .venv/bin/python --editable . --group dev` succeeded. A writable temporary cache was explicitly selected in this sandbox. Tool downloads required approved network access.
- `.venv/bin/collision-warning --help` and `--version` succeeded from outside the source directory. `.venv/bin/python -m pytest -q` passed all five smoke cases. No `PYTHONPATH` adjustment was used.
- `uv build --offline` produced an sdist and a wheel built from that sdist. Installed the wheel into a separate clean CPU environment; all five tests passed there from outside the repository. Temporarily removing that environment's generated console entry point made both help tests fail (pytest exit 1), then the entry point was restored. This is local packaging evidence, not a hosted CI or literal fresh-clone claim.
- Temporary tools also verified `ruff check .`, `ruff format --check .`, and `mypy --strict src/collision_warning`. These tools are not yet project dependencies or locked checks; PR 0B must formalize them. One formatting issue was corrected before the final checks.
- Build artifacts are local, temporary verification outputs; they are not public releases. No public license has been selected, and no model or media assets were added.
- The pre-existing YOLO demo and CUDA environment in the separate `collision-warning` folder were left untouched. No GPU check was executed or CUDA migration attempted.
- Next: PR 0B, capture the existing GPU baseline, generate/commit `uv.lock`, and establish locked local checks. Full Phase 0, clean-clone verification, hosted CI/governance, provenance audit, and Phase 1 remain pending.

---

## 1. Product and scientific contract

### Mission

Given a timestamped monocular forward-facing camera stream, detect and track relevant road users; estimate approach/collision-related quantities using two complementary methods; assess whether predicted relative paths overlap; and produce inspectable, uncertainty-aware visual/logged warnings. Measure both predictive utility and actual end-to-end computational latency.

### Explicit non-goals at inception

- No claim of guaranteed collision avoidance or distance accuracy on arbitrary internet dashcam video.
- No vehicle actuation, braking, steering, production deployment, or safety certification.
- No need for LiDAR, radar, stereo, or IMU at **inference** time; external sensor data may be used as **evaluation ground truth** when its licensing and alignment allow.
- No training a detector or introducing monocular-depth networks, SLAM, cloud infrastructure, ROS2, Kubernetes, microservices, distributed pipelines, or experiment servers merely to make the repository look sophisticated.
- No silent substitution of image-scale proxies for metric meters or physical collision probability.

### Technical realities that shape the architecture

1. **Monocular scale ambiguity:** absolute distance is not observable from arbitrary uncalibrated single-camera imagery. Metric geometry needs known/estimated camera intrinsics, installation geometry, ground-plane assumptions, and validation.
2. **Image-expansion (looming) TTC:** under approximations of constant object dimensions/orientation, stable projection, and dominant motion along the viewing direction, `TTC ~= s / ds_dt` for positive image expansion. This is a *time-to-depth-closure proxy*, not proof that two paths intersect. Avoid computing it for noisy, non-expanding, occluded, or too-short histories.
3. **Ground-plane geometry:** with known camera height, pitch, intrinsics, and a valid road-contact point, estimate camera-relative road position and its change over time. Near-horizon or absent ground contacts lead to unavailable/high-uncertainty measurements, not invented numbers.
4. **Ego motion and scene complexity:** turns, pitch changes, grades, lane geometry, cut-ins, object rotations, missed detections, and tracker identity switches can invalidate naive estimates. Measure/flag the applicable assumptions before relying on estimates.
5. **Risk is a separate layer:** combine independent geometric/image measurements, track quality, and future-path overlap. Inadequate information must produce `UNKNOWN/UNAVAILABLE` rather than implicitly `SAFE`.

### Observable final deliverable

A GitHub repository that a new engineer can clone and run, with a video demo; documented data/model provenance; clear APIs; deterministic CPU tests; opt-in local GPU tests; reproducible evaluation and benchmarks; and a README that states measured results, conditions, known failure modes, and non-safety-certified status. The **engineering evidence** is as important as the demo.

---

## 2. Target architecture — one process, interchangeable components

```text
Timestamped VideoSource
        |
        v
Detector adapter (initially YOLO) -----> Detections + confidence
        |
        v
Tracker adapter (initially ByteTrack) -> Tracks + history + quality
        |
        +---------------------------+
        |                           |
        v                           v
LoomingTtcEstimator         GroundPlaneEstimator
(image expansion, sec)      (camera-relative X,Z; m)
        |                           |
        +---------------------------+
                    |
                    v
           RelativeMotionEstimator
           (camera/ego compensation when available)
                    |
                    v
             RiskAssessor
       (TTC + trajectory/path overlap + evidence)
                    |
                    v
         Results / alerts / overlay / logs
                    |
                    v
          Evaluation + benchmarking
```

**Architectural rule:** the pipeline orchestrates adapters and typed domain values; the numerical geometry and risk logic must not import YOLO, OpenCV UI, or GPU libraries. Video reading must not know the alert policy. Visualization must consume results, not compute them. Dependency direction must remain from entry points/adapters **toward** domain interfaces and pure logic, not the reverse.

### Stable contracts to introduce incrementally

| Contract | Required meaning | Rules |
|---|---|---|
| `Frame` | frame index, source/stream ID, presentation timestamp (seconds), width/height, pixel color space, image payload | preserve source timestamps; document BGR/RGB; never assume processing FPS equals video FPS |
| `Detection` | class, score, `xyxy` box in **pixel** coordinates, source frame | box convention `[x1,y1,x2,y2]`; validate finite coordinates and bounds policy |
| `Track` | stable ID while tracker believes identity persists, observation history, age/quality | reset or invalidate derived velocity on identity change and long gaps |
| `Estimate[T]` | optional value, unit, validity/status, method, quality/evidence | unavailable value is **not** zero; no fake confidence/probability |
| `RelativeState` | camera-frame lateral `X` and longitudinal `Z` (m) and velocities (m/s), with timestamp and validity | publish only when calibrated assumptions suffice |
| `RiskAssessment` | track ID, risk state, TTC evidence, path-overlap evidence, reasons, limitations | distinguish `UNKNOWN`, `NO_CURRENT_WARNING`, and `WARNING`; thresholds are configurable and evaluation-backed |
| `RunMetadata` | config, source hash/ID, model name/version/checksum/license, code commit, environment, timestamps | reproducibility and auditable comparison |

Conventions: **seconds** for times/TTC, **meters** for geometric distances, **m/s** for velocities, **pixels** for boxes, explicit coordinate reference frames, timestamps from the source (not `time.time()` on processing), and explicit optional/invalid states. Keep data structures small (`dataclass`/typed protocols); add runtime schema validation only at external configuration/input boundaries when needed. Don't create twenty empty abstract classes on day one.

### Extension policy

The initial detector is an **adapter**. A future detector, tracking algorithm, depth model, camera calibration backend, warning policy, or output renderer should be replaceable without editing unrelated modules. Do not replace a proven simple function with a plugin framework or dependency-injection container; interfaces follow actual second implementations or clear module boundaries.

---

## 3. What the research says — evidence versus our choices

This document draws on **public engineering documentation and open-source project practices**, not claims about undisclosed internal company architectures. The **Source** column links directly to verifiable material; the **Adoption** column is our project-specific engineering decision.

| Evidence from major organizations / maintained projects | Adoption for this repository |
|---|---|
| **Google:** first establish metrics, simple baselines, solid pipeline infrastructure, and independent tests for ML plumbing [R1]; small, self-contained changes are easier to review, improve, and revert [R2]; reviewers check design, tests, complexity, and docs [R3]. | A measurable baseline and phase acceptance gates; one concern per PR; functionality + tests + documentation together. |
| **PyTorch:** published developer contribution and testing guidance, selective tests, developer/user documentation [R4]. | Document test tiers and commands; test narrow units first, then pipeline integration; no undocumented local-only setup. |
| **Ultralytics:** contribution guidance emphasizes scoped PRs, local testing, CI, reproducible bug reports, documentation, and licensing [R5]. | Lightweight PR template, CI gates, versioned bug reproduction details; isolate the Ultralytics integration behind a detector adapter. |
| **scikit-learn:** publicly maintained contributing/testing guidance and user examples [R6]. | Treat docs/examples/tests as maintained deliverables, not afterthoughts. |
| **Python Packaging Authority + pytest:** `src/` layout avoids accidentally importing local uninstalled code; pytest supports a separate `tests/` tree and `importlib` mode [R7,R8]. | Real installable `src/` Python package, editable local install, tests import the installed package. |
| **Astral `uv`:** `pyproject.toml` + checked-in `uv.lock` for resolved environments; explicit indexes for PyTorch CUDA/CPU variants [R9,R10]. | One chosen dependency manager and lockfile. Avoid undocumented `pip install ...` drift after migration; explicitly manage the RTX 50-series CUDA wheel. |
| **GitHub:** branch rules can require status checks [R11]; Actions guidance recommends least privilege and pinning third-party actions to immutable full commit SHA [R12]. | Required CPU CI before merges, minimal workflow token permissions, verified SHA pins, no untrusted PR code with elevated secrets. |
| **Google ML Test Score:** ML reliability entails data/model/pipeline tests and monitoring, not only code coverage [R13]. **DVC/MLflow:** reproducibility and experiment lineage can be managed explicitly [R14,R15]. | Record dataset/model versions, run config, metrics, and artifacts; start with manifests and files, adopt DVC/MLflow **only** when their additional operations become worthwhile. |
| **Cookiecutter Data Science:** separates raw/intermediate/processed data, models, reports, and source [R16]. | Use this separation selectively; commit manifests/sample synthetic fixtures, not large datasets or downloaded weights. |

**Synthesis, not an appeal to authority:** “Gold standard” means **small coherent design + automated proof + reproducible measurement + truthful limitations**, not copying a gigantic enterprise monorepo. For a single-developer portfolio project, overengineered platforms would violate the simplicity objective.

### Toolchain decisions (proposed, to be recorded as ADR-0001)

- **Dev host:** Windows 11 → WSL2 Ubuntu; keep project under the Ubuntu filesystem (`~/projects/...`), VS Code WSL extension.
- **Python:** target Python 3.12 initially, subject to verifying the working environment and dependencies.
- **Packaging/dependency source of truth:** `pyproject.toml` and committed `uv.lock`; use `uv` after a controlled migration from the already-working `.venv` (do not destroy the environment before documenting it). The lockfile is not a guarantee of bitwise-identical GPU results on different hardware/drivers.
- **Formatting/linting:** Ruff (`ruff check`, `ruff format --check`), one configuration in `pyproject.toml`.
- **Tests:** pytest; pure, deterministic CPU tests default; GPU/model/download/video tests opt-in and marked.
- **Types:** typed public functions and contracts; start with a targeted mypy run over domain/core modules, broaden as integrations stabilize. No need to suppress all errors indiscriminately.
- **Local automation:** pre-commit hooks for fast checks, plus a very short `Makefile` that calls the same canonical `uv run ...` commands. CI is the source of truth, not local hooks alone.
- **CI:** GitHub Actions Ubuntu CPU job on pushes/PRs, no model downloads, no NVIDIA hardware assumption; GPU smoke and sustained benchmarks run on local workstation and are recorded separately.
- **ML dependencies:** install GPU inference support as an **optional extra** when Phase 1 starts; use official `uv` PyTorch explicit `cu130` index mapping for both `torch` and companion packages if needed. Keep the base installation suitable for CPU CI. Test version compatibility before replacing the known working `torch 2.14.1+cu130` environment. `uv` config and commands must agree; do not mix unmanaged pip changes with locked environments.
- **Config:** checked-in example config; paths/thresholds/model ID/frame processing parameters explicit. No secret keys or absolute machine-specific paths in code.
- **Licensing:** audit dependency/model/data licensing **before** deciding repository license or making a public release. In particular, consult Ultralytics' published AGPL/enterprise terms [R5] and the exact pretrained weight/data terms. Do not assume that installing a library automatically settles every derivative-work, redistribution, or commercial-use question; document decisions and obtain appropriate guidance if needed.

---

## 4. Delivery roadmap — each phase is a releasable vertical slice

Each phase requires an issue/short proposal, the smallest coherent implementation, accompanying tests, relevant docs/ADR updates, one reproducible command, an example artifact where licensed, and a measurement report. **Never make the next phase depend on code that passes only on the author's machine.**

| Gate | Deliverable | Evidence before advancing |
|---|---|---|
| **Phase 0 — NOW: repository foundation** | installable package, conventions, environment lock, checks, minimal CLI, typed seed contract, CI, docs | fresh-clone CPU workflow passes; existing GPU baseline documented/rechecked after any migration; branch checks configured |
| **Phase 1: video + detection** | choose authorized sample clips and document scenario/metric plan; frame reader, timestamp preservation, detector adapter and recorded-video CLI, optional CUDA extra | local dashcam demo, detection smoke, sample artifact + model provenance, baseline latency/FPS with methodology |
| **Phase 2: tracking** | ByteTrack adapter, IDs, history, track quality, dropout/reset logic | synthetic unit tests + recorded-video ID/continuity examples; measured tracking impact on throughput |
| **Phase 3: image looming/TTC** | box-scale history, smoothing, derivative/validity gating, `TTC ~= s/ds_dt` when assumptions hold | synthetic known-scale cases and counterexamples (rotation, occlusion, no expansion); unavailable status tested |
| **Phase 4: calibrated road geometry** | intrinsics/height/pitch config, ground-contact projection, camera-relative lateral/longitudinal estimates | geometric tests against synthetic projections; calibration provenance; evaluate error vs reference if available |
| **Phase 5: relative motion + path overlap** | time-differenced relative state, ego-motion limitations/compensation, projected path intersection | synthetic straight/adjacent/crossing/cut-in cases; documented failure cases; no units/frame confusion |
| **Phase 6: risk + alert pipeline** | explicit policies, severity/reasons, visual/audio/log output, uncertainty/unknown handling | false-alert and missed-alert scenarios on held-out clips; warnings do not run on invalid estimates |
| **Phase 7: evaluation + optimization** | benchmark dataset manifest and harness, ablation between looming vs geometry vs hybrid, profiling, docs/demo | detection/tracking, TTC, false-alert/miss, latency p50/p95, throughput, hardware/model/config all reported |

**Dataset principle:** choose legal, annotated/reference footage appropriate to each target metric. A clip with only boxes cannot validate metric depth or ground-truth TTC. Keep video sequences separated during evaluation to avoid near-duplicate leakage. Any reference radar/LiDAR/ground-truth measurements are evaluation-only: the inference pipeline remains monocular RGB. Write dataset cards documenting scene types, labels, reference alignment, calibration, licensing, and blind spots.

**Performance reporting rule:** measure cold start separately from warmed inference; decode, detection, tracking, estimation, overlay, and total end-to-end stages separately; use true presentation timestamps for motion; account for CUDA's asynchronous execution when benchmarking (synchronize for elapsed GPU measurements); log p50/p95 latency, processed FPS, original video FPS, frame drops, resolution, batch size, hardware/driver, model and config. A working design target may be 30 processed FPS on the RTX 5070 Ti **but this is an unverified aspiration, not a current claim or safety requirement**.

---

## 5. Phase 0 — precise repository bootstrap specification

### 5.1 Design target

A colleague should be able to clone the repo, understand the mission and restrictions, install the non-GPU developer environment using **one canonical path**, run one CLI help/smoke command, run all CPU checks, and see exactly how a later Phase 1 adapter fits into the package. Bootstrap adds **no imaginary output** for distance/TTC/risk and **no false green checks**.

### 5.2 Target tree (future-facing; do not generate empty speculative implementations)

```text
monocular-collision-warning/
├── .github/
│   ├── workflows/ci.yml
│   └── PULL_REQUEST_TEMPLATE.md
├── .gitignore
├── .gitattributes
├── .editorconfig
├── .pre-commit-config.yaml
├── .python-version
├── README.md                     # 2-minute project overview, quickstart, current status, caveat
├── HANDOFF.md                    # this document (or docs/HANDOFF.md)
├── CONTRIBUTING.md               # setup, local checks, PR/test conventions
├── pyproject.toml                # package metadata, deps, lint/test/type/tool config, CLI entry
├── uv.lock                       # commit; generated, never manually edited
├── Makefile                      # thin aliases; no parallel dependency definitions
├── src/
│   └── collision_warning/
│       ├── __init__.py
│       ├── cli.py                # help/diagnostics; actual video command arrives Phase 1
│       ├── domain/              # introduced as typed contracts become necessary
│       │   └── __init__.py
│       └── ...                  # Phase 1+: io/, detection/, tracking/, estimation/, risk/, viz/, evaluation/
├── tests/
│   ├── unit/
│   │   └── test_package_smoke.py
│   ├── integration/             # populated with real interfaces; no empty passing tests
│   ├── fixtures/                # tiny generated synthetic fixtures only
│   └── conftest.py              # shared fixtures only if needed
├── configs/
│   └── README.md                # explain versioned configs; actual config added with feature
├── data/
│   └── README.md                # provenance instructions; raw videos ignored
├── models/
│   └── README.md                # fetch/checksum/license policy; weights ignored
├── outputs/
│   └── .gitkeep                 # results ignored except explicit illustrative examples
├── docs/
│   ├── architecture.md
│   ├── evaluation-plan.md
│   ├── development.md
│   ├── resources.md             # short adoption ledger; not a dependency shopping list
│   ├── third-party-licenses.md
│   └── adr/
│       ├── README.md            # accepted/proposed/superseded ADR convention
│       └── 0001-repository-foundation.md
└── scripts/                      # only real repeatable helper scripts; never business logic
```

**Tree is a design map, not a request to create empty folders/files blindly.** Each future feature should land where its responsibility belongs. Avoid root-level `main.py`, `utils.py`, `model.py`, and notebooks as production logic; notebooks are optional exploratory clients of the installed package. Avoid repeated per-module copies of schema types or config parsers.

### 5.3 Build Phase 0 as FOUR small PRs/commits

**PR 0A — Define the contract and installable package**

- Write concise README with problem, image-only inference restriction, current status, architecture link, safety/research disclaimer, roadmap, and quickstart.
- Add this handoff; `docs/architecture.md` with a diagram and module boundaries; ADR-0001 explaining `src` layout, `uv`, CPU CI + opt-in GPU, and what was deliberately deferred.
- Add `pyproject.toml` using a standard build backend with `src/` discovery and an actual console entry point, e.g. `collision-warning --help`; choose/test Python target against workstation.
- Add `src/collision_warning/__init__.py`, minimal CLI with useful `--help`/version, and one **real** smoke test that imports the installed package and exercises the CLI. No YOLO import at package import time.
- Add license audit notes before selecting a public repository license; no unverified `LICENSE` boilerplate.
- **Gate:** editable install succeeds; `collision-warning --help` works from a clean environment; smoke test fails if package/entry point breaks.

**PR 0B — Reproducibility + local checks**

- Capture current working GPU environment in a local baseline note/command output; record relevant `python --version`, `nvidia-smi`, `pip freeze`/versions, and `torch` CUDA check. No machine IDs or private paths in the repo.
- Adopt `uv` as the **only** project dependency source of truth. Commit `uv.lock`. Explicitly document how to preserve/recreate the known working RTX setup before migrating Phase 1 GPU dependencies. Prefer base/dev CPU-safe deps now; don't install a second CUDA stack just for bootstrap.
- Configure Ruff, pytest `--import-mode=importlib`, mypy's narrow initial target, and pre-commit. Add `.editorconfig`, `.gitattributes`, `.gitignore` for `.venv/`, `__pycache__/`, caches, `.env`, datasets, outputs, and model weights.
- Add thin Makefile or equivalent: `setup`, `lint`, `format-check`, `typecheck`, `test`, `check` (commands map directly to `uv sync --locked`, `uv run --locked ...`). No broad auto-fixing in CI.
- **Gate:** same commands work twice without dependency churn or untracked binary artifacts; lockfile is not modified by a locked check.

**PR 0C — GitHub governance + CI**

- Add `.github/workflows/ci.yml` on push/PR: checkout; install documented Python and `uv`; `uv sync --locked` for base/dev environment; lint; format check; type check; deterministic CPU pytest; build/import or CLI smoke. Define explicit job names and minimal `permissions: contents: read`; pin actions to **verified full SHAs**, with version comments/update policy, rather than inventing hashes.
- No credentials, training data, network-fetched model weights, CUDA, or WSL-specific paths in CPU CI. No privileged `pull_request_target` execution of PR code.
- Add PR template: why, scope, commands + results, tests, docs/config changes, reproducibility/artifacts, risk/failure modes, licensing if applicable. Add `CONTRIBUTING.md` with branch naming and required steps.
- Once CI job names are established, configure `main` protection/ruleset: require PR and passing status check(s), block force-push/deletion. For a solo maintainer, an external reviewer approval can be optional until there is a reviewer; **never** waive checks silently.
- **Gate:** open a test PR and verify a deliberately broken test/lint blocks merge; fix it and verify checks pass.

**PR 0D — Data/model hygiene + final bootstrap audit**

- `data/README.md` defines external/raw/interim/processed convention **when those stages exist**, source URL/license/access date, sequence split, checksum, reference timestamp/calibration metadata, privacy/redaction requirements.
- `models/README.md` defines model ID, upstream version, exact file URL or approved acquisition process, SHA-256, license, local path, and no downloading during import/tests. Don't commit weights.
- `docs/evaluation-plan.md` defines metrics, a versioned scenario/test-clip manifest (including negative controls), and withheld success claims; simple local JSON/CSV run manifest template (code commit, input checksum, config, model checksum, hardware, versions, metrics).
- `docs/third-party-licenses.md` tracks library, model, dataset separately. Explicit Ultralytics review gate before public release. No copyrighted video/screenshots added without redistribution rights.
- Add a **short** `docs/resources.md` candidate/adoption ledger based on the companion `Useful-tools-updated.md` research library; include the three directory links, the decision template in §8, and only candidates actually under consideration. Do not install or copy in directory listings as requirements.
- Review docs links and clean-clone setup; tag `v0.1.0-foundation` **only after** successful gates if a baseline tag is useful.
- **Gate:** repo contains no large binaries/secrets; docs can take a stranger from clone to passing checks; no fake performance/distance claims.

### 5.4 Canonical developer experience (specification, not proof of current implementation)

After PR 0B, the README should allow the following **from an Ubuntu/WSL terminal in the repository root**:

```bash
# Once uv is installed per the documented official method:
uv sync --locked                    # install locked base + default dev group
uv run --locked collision-warning --help
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy src/collision_warning/domain  # adapt to actual populated modules
uv run --locked pytest -q
```

If `domain/` does not yet contain implementation, type-check actual `src/collision_warning` or a real small core module instead. Do not commit broken placeholder commands. `make check` may aggregate these but must not hide failures. Later GPU setup must have its own documented extra/command and local `pytest -m gpu`; **do not** pretend base `uv sync` alone recreates the full CUDA environment.

For Phase 1 CUDA packaging, follow the [official uv + PyTorch guide](https://docs.astral.sh/uv/guides/integration/pytorch/), including `explicit = true` on the PyTorch index and source mapping for each selected PyTorch package. Ensure the documented `uv --extra` command is tested on this Ubuntu/RTX setup and that CPU CI can still install without the GPU extra.

### 5.5 Required test taxonomy

| Tier | Trigger | Allowed requirements | Examples |
|---|---|---|---|
| Unit | every PR | CPU, no network, tiny synthetic data, deterministic | timestamp ordering, coordinates/units validation, derivative math, invalid input handling |
| Integration | every PR when lightweight | CPU, tiny generated or redistributable fixture, fake adapters | frame → detector stub → track stub → results manifest |
| GPU smoke | local/opt-in | working CUDA + pinned model weights, verified checksum | model loads, single-frame prediction, output shape/device |
| Video/evaluation | local or scheduled later | licensed recorded clips, fixed dataset/config | compare stage outputs and annotated references |
| Performance/regression | explicit benchmark runs | named hardware, warm-up protocol, repeated runs | stage timings and end-to-end p50/p95; avoid flaky fixed FPS CI gates |

Use marker names `gpu`, `integration`, `slow`, `benchmark` where appropriate; default pytest must explicitly skip local-only GPU/benchmark tests. No `pytest.skip` masking an unexpectedly broken core unit test. Once added, geometry and TTC test data should be analytic/synthetic **with known correct answers**, and recorded-video tests should be separate from ground-truth evaluation.

### 5.6 Contribution rules to follow from day one

1. Every change has one sentence of purpose, an explicit scope, and an acceptance test. Prefer a focused PR/commit to an all-at-once refactor [R2].
2. Pure numerical methods accept data and parameters, return values/status, and have deterministic examples. No hidden global config, direct filesystem access, `cv2.imshow`, logger-only return values, or implicit CUDA side effects.
3. No generic helpers until a real second use case appears. Favor descriptive names and a shallow tree over ceremony.
4. Tests should fail for a plausible bug, not merely check that functions exist. Fix regressions with a test first when practical [R3].
5. No feature is done without an example invocation, relevant docs, known limitations, and a recorded metric or explicit reason it cannot yet be measured.
6. Keep external model/data licenses and checksums alongside provenance, **not** buried in a notebook or local memory.
7. If a result is unknown, represent `UNKNOWN`; never infer `SAFE` from missing measurements, nor claim metric distance from image-only scale without calibration.
8. Prefer an ADR for consequential decisions; mark superseded ones, do not silently rewrite history. Include a short decision, context, options, trade-offs, and consequences.
9. Keep `README.md` fast for newcomers; detailed contracts/decisions belong under `docs/`. Update HANDOFF state at each phase boundary.
10. Code agents may propose and execute **one bounded phase task at a time**. They must run/report available tests, describe unexecuted GPU checks, and must not invent completed outcomes.

### 5.7 Phase 0 definition of done (checkboxes are intentionally not pre-checked)

- [x] Package can be installed from clean clone without setting `PYTHONPATH` manually.
- [x] One locked, documented CPU environment installs; no accidental `uv.lock` rewrite.
- [x] `collision-warning --help` and a meaningful smoke test run.
- [x] Ruff lint and format, targeted type check, and pytest all pass locally.
- [ ] GitHub Actions CPU CI passes; an intentional broken check demonstrably fails the job.
- [ ] `main` is protected by applicable PR/status-check rules.
- [ ] No datasets, model weights, generated outputs, secret files, or private media are accidentally tracked.
- [ ] This handoff, README, architecture, contributing guidance, evaluation plan, resource/adoption ledger, and initial ADR agree.
- [x] Existing RTX 5070 Ti/CUDA success is recorded; if migration has happened, its GPU smoke is re-run, not assumed.
- [ ] Phase 1 has a small actionable issue with exact expected inputs, outputs, tests, and demo command.

---

## 6. Evaluation strategy written *before* feature implementation

| Layer | Track these as appropriate | Known traps |
|---|---|---|
| Detection | per-class precision/recall or AP on labeled footage, confidence calibration if evaluated | a visually plausible bus photo is not validation |
| Tracking | ID continuity/switches and a documented tracking metric (e.g., IDF1/HOTA where labels support it) | bouncing track IDs corrupt temporal TTC |
| Looming TTC | error vs independently derived/reference TTC on approaching cases; percent valid/unavailable; stability | scale rate from a changing box due to object rotation ≠ physically valid TTC |
| Geometry | lateral and longitudinal error (m), uncertainty across distances, coverage, sensitivity to camera parameters | near-horizon singularity; unknown calibration; occluded feet/wheels |
| Risk/alert | event-level false warnings/misses, warning lead time, breakdown by scene type, unknown/abstention rate, warning state transitions/oscillation; report rate denominators (e.g., per annotated event or per hour of reviewed footage) | TTC alone does not establish collision-path intersection; frame counts are not equivalent to distinct warning events; thresholds need evaluation |
| Runtime | stagewise warm/cold timing, p50/p95 E2E latency, processed FPS, frame-drop rate, peak memory | GPU async timing, decode vs compute, original FPS vs processing FPS |

In `docs/evaluation-plan.md`, define a compact scenario matrix up front: approaching same-lane targets (positive candidates), adjacent-lane objects (negative controls), stationary objects, crossing pedestrians, cut-ins, braking/acceleration, occlusions/ID switches, turns/camera shake, and conditions such as night, rain and glare **if licensed clips cover them**. Note expected output and whether meaningful reference TTC/distance/warning labels actually exist for each clip; do not call visual appearance or regional weather-API data ground truth. Annotate contiguous warning **events**, not only individual flagged frames, to evaluate false-alarm frequency, missed risky events, lead time and flicker. These are proposed evaluation cases, not a claim that data has been collected.

Keep a small fixed **development** set and a separate **held-out evaluation** set; record videos/sequences and legal access rather than committing huge assets. Start with clearly enumerated synthetic cases before selecting external datasets. Any model comparison must hold input resolution, source clips, device, warmup, and metric definitions constant. Publish failures and uncertainties alongside positive cases.

A future `runs/<run-id>/` (gitignored) could contain `manifest.json`, `metrics.json`, `config.yaml`, `events.jsonl`, and optionally an authorized annotated clip. Introduce DVC if large dataset/model versioning becomes hard to manage [R14]; introduce MLflow if comparing/managing many experiment runs creates genuine friction [R15]. Neither is a Phase 0 prerequisite.

---

## 7. Decisions deliberately deferred

| Decision | When/how to decide |
|---|---|
| Exact detector weights/version and Ultralytics license impact | Phase 1, after recorded license audit and reproducible smoke |
| Ground-contact localization (bottom of bounding box vs segmentation/keypoint) | Phase 4, compare on labeled camera/road scenes |
| Camera calibration source and metric reference dataset | Phase 4 proposal; absent calibration means no metric-distance claims |
| Motion/ego compensation method (visual odometry, optical flow, other inputs) | Phase 5; first state assumptions and measure rotation/grade failures |
| Temporal smoothing / derivative filters | Phase 3/5 on synthetic and validation footage; include noise/lag trade-off |
| Warning thresholds and classes | Phase 6 based on actual measured cases, not arbitrary red/yellow labels |
| DVC/MLflow, Docker, ROS2, ONNX/TensorRT, C++ optimization | Only after measured need; record ADR explaining maintenance cost |
| Production-grade safety compliance | Out of scope. Would require an entirely different validation and assurance program. |

---

## 8. Research library → explicit adoption decisions

This section incorporates the companion **`Useful-tools-updated.md` (2026-10-01)**. Its source content describes three **curated directories/collections**, not three installable libraries. The applicability, priorities and system design below are **our project decisions**, not claims that the directories or cited companies endorse our architecture. The library verified the main indexes and selected destinations as of 2026-10-01; that is **not** proof that every underlying API, dataset, tutorial, license, price or geographic service remains suitable. Check official upstream material at the actual point of adoption. [Resource library: introductory note, A–E.]

### 8.1 What to consult, when (not a backlog of integrations)

| Source collection | Relevant entry from the resource library | Our decision / phase | What **not** to infer |
|---|---|---|---|
| [API Vault](https://apivault.dev/) / [catalog](https://github.com/exa-studio/ApiVault) | A2 ML/CV: Roboflow Universe for possible footage/annotations/model discovery | **Phase 1 candidate discovery only**, with license, data provenance, sequence splits and permitted redistribution checked against provider and dataset pages | A catalog listing does not mean data/model availability, correctness or permission to use it. Hosted CV APIs are not our core perception engine. |
| [Applied ML](https://github.com/eugeneyan/applied-ml) | B1 video/temporal case studies: Google real-time sign-language detection, RepNet; Deepomatic labeling-quality example; Tesla talk for domain inspiration | **Phases 1–3:** prompts for frame-to-sequence reasoning, label auditing and engineering trade-offs; seek originals by exact titles | These are research precedents in different tasks, **not** verified tracker/TTC code or a claim to reproduce Tesla's system. |
| Applied ML | B2 Pinterest GPU inference; Uber compression | **Phase 7:** study benchmark methodology and accuracy/performance trade-offs *after* a measured baseline | Neither establishes this project's FPS, latency, or a need for quantization. |
| Applied ML | B3 Nubank model monitoring/train-serve skew; B4 Google ML rules, DoorDash monitoring and Nubank operational alerting | **Phases 0, 6–7:** reproducible baselines and experiment traceability; operational-alert lessons only as analogies | **ML operations alerts are not driver collision warnings**. Independently test safety-facing warning logic and event behavior. |
| [Build Your Own X](https://github.com/codecrafters-io/build-your-own-x) | C1 OpenCV AR; C2 Flask/HTTP; C3 spatial partitioning/physics; C4 video/3D; C5 NN internals | **LEARNING / OPTIONAL** only if a concrete problem warrants it; use OpenCV/FFmpeg and a maintained service framework if needed | AR examples aren't road overlays; game-engine collision checks aren't monocular TTC; do **not** rebuild a web server, codec, physics engine or PyTorch. |
| API Vault A1 | Adzuna/Arbeitnow and other jobs sources | **Separate, optional** portfolio-scope evidence: timestamped, deduplicated *sample* of junior CV/perception vacancies | A sample isn't representative of the entire labor market, nor a Phase 0 install requirement. |
| API Vault A3–A5 | Mapping/traffic, weather and authorized vehicle telemetry | **Defer to evidence-backed V2/V3 proposals**, if a metric or user-facing need appears | GPS/maps aren't object range ground truth; location-level weather isn't clip-level labels; vehicle telemetry isn't presumed live, authorized or accessible. |

**Core rule from the library:** temporal risk calculation and measurements must be implemented and inspectable in **our own code**, rather than outsourced to a hosted image API. Keep the MVP offline and single-process. Do not add mapping, weather, telemetry, cloud endpoints or a dashboard to make the architecture look larger.

### 8.2 A tiny, auditable research/adoption ledger

At Phase 0D, establish `docs/resources.md` with a link to this section, the three directory indexes above and a few *candidate-only* entries, **not** a copied directory. When actually trialing a tool, dataset, model, API, or article-derived method, use this record; update its decision status and date on adoption/rejection:

```text
Name and direct official/upstream URL:
Type: dataset | model | library | API | paper/case study | tutorial | benchmark
Discovered via: API Vault | Applied ML | Build Your Own X | independent research
Documented upstream capability (fact; cite actual provider/publication):
Intended use in our pipeline (our proposal, including target phase/metric):
Access / license / region / provenance / privacy / maintenance checked: date + result
Alternatives and reason to prefer or defer this candidate:
Priority: NOW | NEXT | OPTIONAL | LEARNING
Decision: candidate | tried | adopted | rejected | deferred; rationale and ADR if consequential
Reproduction: version, exact URL/hash, retrieval steps, test or experiment ID (if tried)
```

**Gate:** if access rights, licensing, provenance, reference quality, or a measurable project need are unclear, leave the candidate **deferred**. A link alone is never approval to use a dataset or ship a model. Retain licensed raw/annotated video outside Git and record acquisition, splits and checksums in manifests. When comparing implementations, preserve common clips, resolution, warm-up, precision/accuracy conditions and hardware; report failed optimizations and uncertainty rather than speculative benchmark values.

### 8.3 Three distinct notions of an alert

1. **Driver-facing warning event:** measured from risk/ground-truth scenario evidence with true/missed events, false alerts per declared exposure, lead time, warning stability/flicker and abstention/`UNKNOWN` behavior. No arbitrary thresholds are deemed valid by visual plausibility alone.
2. **Operational ML alert:** about pipeline health, drift, missing input, exceptions, memory or latency, drawing on production-ML examples only by analogy. Never equate a successful health alert with safe driver-warning behavior.
3. **Demonstration overlay:** renders an already decided risk/status from the core, and never secretly computes TTC or upgrades `UNKNOWN` to `SAFE`.

The research library's physics/AR/server tutorials do not remove our scientific constraints: a monocular image alone does not give arbitrary metric range, and a projected bounding box overlap is not equivalent to validated real-road collision risk.

---

## 9. Instructions for the next contributor / coding agent

**Current next task:** PR 0A and PR 0B from §5.3 have passed their local gates; PR 0C's local implementation is prepared. Finish **only PR 0C's hosted gate** once the intended GitHub repository and administration access are available. Before any remote write, inspect its contents/settings and preserve unrelated work and stronger protection. Verify actual hosted passing/failing jobs and merge enforcement. PR 0D remains a later task. Run and report checks actually executed, state blockers, and do not present a future phase as completed. The remaining Phase 0 acceptance boxes are not proof of current functionality.

**When resuming later, report in this order:** phase/state; changed files; commands and actual results; outputs/artifacts (with location and licensing); decisions/ADRs; next smallest task; unresolved risks. Update the top **Status** and checkboxes in this handoff whenever a phase closes.

Suggested very first issue title: **`chore: initialize installable src-layout repo and engineering docs`**.

---

## 10. Public research references (accessed 2026-10-03)

These are primary-source/public project documents. Statements in §3 summarize observed public practices; choices elsewhere are **proposals for this project**, not statements that each named company uses this exact stack or directory tree.

- [R1] Google, [Rules of Machine Learning](https://developers.google.com/machine-learning/guides/rules-of-ml) — metrics, simple first pipeline, independent tests.
- [R2] Google, [Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html) — scope/review/rollback advantages.
- [R3] Google, [What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html) — design, tests, complexity and documentation.
- [R4] PyTorch, [CONTRIBUTING.md](https://github.com/pytorch/pytorch/blob/main/CONTRIBUTING.md) — testing and developer guidance.
- [R5] Ultralytics, [Contributing guide](https://docs.ultralytics.com/help/contributing/) — change workflow, CI, documentation, licenses.
- [R6] scikit-learn, [Developer/contributing guide](https://scikit-learn.org/dev/developers/contributing.html) — maintained tests, docs, examples.
- [R7] Python Packaging User Guide, [`src` vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) — installed-code isolation.
- [R8] pytest, [Good integration practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html) — source/test layout and import modes.
- [R9] Astral, [uv working on projects](https://docs.astral.sh/uv/guides/projects/) and [locking/syncing](https://docs.astral.sh/uv/concepts/projects/sync/) — declarative and locked dependencies.
- [R10] Astral, [Using uv with PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/) — explicit CPU/CUDA index patterns, including `cu130`.
- [R11] GitHub, [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) — PR and required status-check governance.
- [R12] GitHub, [Secure use reference for Actions](https://docs.github.com/en/actions/reference/security/secure-use) — immutable SHA pinning and workflow security.
- [R13] Breck et al. (Google), [The ML Test Score](https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/) — broader ML system tests and monitoring.
- [R14] DVC, [User Guide](https://doc.dvc.org/user-guide) — versioned data/pipelines/experiments when scale warrants.
- [R15] MLflow, [Tracking](https://mlflow.org/docs/latest/ml/tracking/) — run parameter/metric/artifact lineage.
- [R16] DrivenData, [Cookiecutter Data Science](https://cookiecutter-data-science.drivendata.org/) — example separation of data/source/reports.
- [R17] Ruff, [Formatter](https://docs.astral.sh/ruff/formatter/) and [Linter](https://docs.astral.sh/ruff/linter/) — consistent lightweight checks.

**Companion source note:** `Useful-tools-updated.md` is a maintained research/reference collection as of 2026-10-01; §8 applies its recommendations to this repository. Its three underlying collections are directories, not toolchain dependencies. Check direct upstream documentation on adoption.

**Final handoff rule:** the repo's architecture is successful only when a Phase 3 TTC function, Phase 4 ground-plane estimator, and Phase 6 risk policy can each be developed, mocked, tested, benchmarked, and explained **without modifying the unrelated components**. That, rather than folder count or badge count, is the standard we are building toward.
