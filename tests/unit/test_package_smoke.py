"""Check installed imports and the real console script outside the source tree."""

import subprocess
import sys
import sysconfig
from importlib.metadata import version
from pathlib import Path

import pytest


def test_package_imports_in_isolated_interpreter(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "from collision_warning.cli import main; assert callable(main)",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize("arguments", [[], ["--help"]])
def test_installed_console_script_help(tmp_path: Path, arguments: list[str]) -> None:
    executable = Path(sysconfig.get_path("scripts")) / "collision-warning"
    result = subprocess.run(
        [str(executable), *arguments],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert "usage: collision-warning" in result.stdout
    assert "--version" in result.stdout
    assert "Phase 1 video detection" in result.stdout
    assert result.stderr == ""


def test_installed_console_script_version(tmp_path: Path) -> None:
    executable = Path(sysconfig.get_path("scripts")) / "collision-warning"
    result = subprocess.run(
        [str(executable), "--version"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == (
        f"collision-warning {version('monocular-collision-warning')}"
    )
    assert result.stderr == ""


def test_installed_console_script_rejects_unknown_option(tmp_path: Path) -> None:
    executable = Path(sysconfig.get_path("scripts")) / "collision-warning"
    result = subprocess.run(
        [str(executable), "--unknown-option"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 2
    assert "unrecognized arguments: --unknown-option" in result.stderr
    assert result.stdout == ""
