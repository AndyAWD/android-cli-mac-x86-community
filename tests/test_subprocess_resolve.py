from __future__ import annotations

import sys
from pathlib import Path

import pytest

from android_cli_mac_x86_community.tools._subprocess import (
    ToolNotFoundError,
    resolve,
)


def test_resolve_absolute_existing(tmp_path: Path):
    exe = tmp_path / "thing"
    exe.write_text("")
    assert resolve(exe) == exe


def test_resolve_absolute_missing_raises(tmp_path: Path):
    with pytest.raises(ToolNotFoundError):
        resolve(tmp_path / "ghost")


def test_resolve_finds_exe_suffix_on_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """On Windows, callers pass extensionless paths (e.g. .../adb)."""
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("PATHEXT", ".COM;.EXE;.BAT")
    real = tmp_path / "adb.exe"
    real.write_text("")
    bare = tmp_path / "adb"
    assert resolve(bare) == real


def test_resolve_does_not_probe_suffix_on_unix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """On non-Windows, an absolute path that lacks the file must error."""
    monkeypatch.setattr(sys, "platform", "linux")
    (tmp_path / "adb.exe").write_text("")
    with pytest.raises(ToolNotFoundError):
        resolve(tmp_path / "adb")
