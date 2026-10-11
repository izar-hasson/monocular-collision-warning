"""Hash failures must never promote partial downloads to installable wheels."""

import hashlib
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "download_pytorch_wheels",
    Path(__file__).resolve().parents[2] / "scripts/download_pytorch_wheels.py",
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.mark.parametrize("valid", [True, False])
def test_download_promotes_only_verified_payload(monkeypatch, tmp_path, valid):
    payload = b"verified fixture" if valid else b"corrupt"

    def fake_curl(arguments, *, check):
        assert check
        Path(arguments[arguments.index("--output") + 1]).write_bytes(payload)

    monkeypatch.setattr(MODULE.subprocess, "run", fake_curl)
    target = tmp_path / "torch.whl"
    expected = hashlib.sha256(b"verified fixture").hexdigest()
    if valid:
        MODULE.download("https://download.pytorch.org/test", expected, target)
        assert target.read_bytes() == payload
        assert not target.with_suffix(".whl.part").exists()
    else:
        with pytest.raises(ValueError, match="Downloaded wheel hash mismatch"):
            MODULE.download("https://download.pytorch.org/test", expected, target)
        assert not target.exists()
        assert target.with_suffix(".whl.part").read_bytes() == payload


def test_verified_existing_wheel_never_downloads(monkeypatch, tmp_path):
    def unexpected_download(*args, **kwargs):
        pytest.fail("Existing verified wheels must be reused")

    monkeypatch.setattr(MODULE.subprocess, "run", unexpected_download)
    target = tmp_path / "torch.whl"
    target.write_bytes(b"verified fixture")
    expected = hashlib.sha256(target.read_bytes()).hexdigest()
    MODULE.download("https://download.pytorch.org/test", expected, target)
    with pytest.raises(ValueError, match="Existing wheel hash mismatch"):
        MODULE.download("https://download.pytorch.org/test", "0" * 64, target)
    assert target.read_bytes() == b"verified fixture"


def test_acquire_selects_cuda_variant_when_cpu_variant_comes_first(
    monkeypatch, tmp_path
):
    lockfile = tmp_path / "uv.lock"
    entries = []
    for name in ("torch", "torchvision"):
        filename = f"{name}-test%2Bcu130-cp312-cp312-manylinux_2_28_x86_64.whl"
        source_url = f"https://download-r2.pytorch.org/whl/cu130/{filename}"
        gpu_registry = "https://download.pytorch.org/whl/cu130"
        entries.extend(
            [
                f'[[package]]\nname="{name}"\nsource={{registry="https://pypi.org/simple"}}\nwheels=[]',
                f'[[package]]\nname="{name}"\nsource={{registry="{gpu_registry}"}}\n'
                f'wheels=[{{url="{source_url}",hash="sha256:{"0" * 64}"}}]',
            ]
        )
    lockfile.write_text("\n".join(entries))
    calls = []
    monkeypatch.setattr(MODULE, "download", lambda *args: calls.append(args))
    MODULE.acquire(lockfile, tmp_path / "wheels")
    assert len(calls) == 2
    assert all(
        url.startswith("https://download.pytorch.org/whl/cu130/") for url, _, _ in calls
    )
    assert all("+cu130" in target.name for _, _, target in calls)
