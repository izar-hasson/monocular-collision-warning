# Development and GPU baseline

Captured 2026-10-04 before changing the project's CPU tooling. The pre-existing
YOLO demo environment was inspected in place; its installed packages were not
changed. These are environment checks, not validated video tracking, TTC,
geometry, warning accuracy, or throughput.

| Item | Observed baseline |
| --- | --- |
| Host | Windows / WSL2 Ubuntu 24.04.5 LTS |
| Kernel | 6.18.40.1-microsoft-standard-WSL2 |
| Python | 3.12.3 |
| GPU | NVIDIA GeForce RTX 5070 Ti |
| Driver reported by nvidia-smi | 616.64 |
| GPU memory reported by nvidia-smi | 16303 MiB |
| PyTorch | 2.14.1+cu130 |
| PyTorch CUDA build | 13.0 |
| torchvision | 0.29.1+cu130 |
| Ultralytics | 8.4.172 |
| OpenCV package | opencv-python 5.0.0.93 |
| NumPy | 2.5.2 |
| pip in the pre-existing demo environment | 26.2.1 |
| uv in the pre-existing demo environment | Not installed |
| uv used for repository tooling | 0.12.23 |

Outside the execution sandbox, `torch.cuda.is_available()` returned `True`,
compute capability was `(12, 0)`, and multiplying two 2×2 CUDA tensors of ones
returned `[[2.0, 2.0], [2.0, 2.0]]`. GPU access was blocked inside the sandbox;
that result reflects execution permissions, not a changed CUDA installation.
No YOLO prediction was rerun in PR 0B. The earlier image prediction remains
historical evidence in [HANDOFF.md](../HANDOFF.md).

## Capture and preserve

Keep raw command output local under gitignored `local-baselines/`, including
`python --version`, `python -m pip freeze`, selected package versions,
`nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader`,
and the CUDA availability/capability/tensor-multiplication results. Use the
existing environment's Python executable explicitly. Do not publish machine IDs,
GPU UUIDs, user paths, private package URLs, or environment variables.

A pip freeze snapshot documents installed versions; it is not a complete
recreation recipe for CUDA packages. Driver/platform state, exact wheel indexes,
checksums, and package compatibility also matter.

## Migration gate for Phase 1

1. Preserve the existing working environment and its snapshot.
2. Define/test an optional GPU extra in a new environment. Use the official
   explicit cu130 PyTorch index and source mappings for every selected torch
   companion package; do not assume arbitrary versions are compatible.
3. Verify the base CPU sync still works without the extra. Document the exact
   locked GPU setup command only after testing it on this workstation.
4. Rerun CUDA tensor and detector smoke checks with verified local weights before
   replacing any baseline. Record new versions, model checksum/license, outputs,
   and failures. Do not mix unmanaged pip modifications with locked uv setup.

The current `uv sync --locked` creates only this repository's CPU developer
environment. It does not recreate the preserved CUDA stack. Consult the
[official uv/PyTorch guide](https://docs.astral.sh/uv/guides/integration/pytorch/)
when implementing Phase 1; this is a deferred migration plan.
