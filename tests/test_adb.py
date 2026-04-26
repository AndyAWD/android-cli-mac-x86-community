from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from android_cli_mac_x86_community.tools import adb


@pytest.fixture
def captured_run(monkeypatch: pytest.MonkeyPatch):
    """Replace tools._subprocess.run with a recorder that returns a fake ToolResult."""
    from android_cli_mac_x86_community.tools import _subprocess

    calls: list[tuple] = []

    def fake_run(executable, args, **kwargs):
        calls.append((Path(executable).name, list(args), kwargs))
        return _subprocess.ToolResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("android_cli_mac_x86_community.tools.adb.run", fake_run)
    return calls


def test_install_single_apk(fake_sdk, captured_run):
    adb.install(["app.apk"])
    name, args, _ = captured_run[0]
    assert name == "adb"
    assert "install" in args
    assert "-r" in args
    assert args[-1] == "app.apk"


def test_install_multiple_uses_install_multiple(fake_sdk, captured_run):
    adb.install(["a.apk", "b.apk"])
    _, args, _ = captured_run[0]
    assert "install-multiple" in args
    assert args[-2:] == ["a.apk", "b.apk"]


def test_install_with_serial_passes_dash_s(fake_sdk, captured_run):
    adb.install(["app.apk"], serial="emulator-5554")
    _, args, _ = captured_run[0]
    assert args[:2] == ["-s", "emulator-5554"]


def test_start_activity_builds_am_command(fake_sdk, captured_run):
    adb.start_activity("com.example/.MainActivity")
    _, args, _ = captured_run[0]
    assert args[0] == "shell"
    assert "am start -n com.example/.MainActivity" in args[1]


def test_start_activity_debug_flag(fake_sdk, captured_run):
    adb.start_activity("com.example/.M", debug=True)
    _, args, _ = captured_run[0]
    assert "-D" in args[1]


def test_emu_kill_targets_serial(fake_sdk, captured_run):
    adb.emu_kill("emulator-5554")
    _, args, _ = captured_run[0]
    assert args == ["-s", "emulator-5554", "emu", "kill"]
