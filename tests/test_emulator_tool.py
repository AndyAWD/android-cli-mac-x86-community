from __future__ import annotations

from pathlib import Path

import pytest

from android_cli_mac_x86_community.tools import emulator


@pytest.fixture
def captured_run(monkeypatch: pytest.MonkeyPatch):
    from android_cli_mac_x86_community.tools import _subprocess

    calls: list[tuple] = []

    def fake_run(executable, args, **kwargs):
        calls.append((Path(executable).name, list(args), kwargs))
        return _subprocess.ToolResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(
        "android_cli_mac_x86_community.tools.emulator.run", fake_run
    )
    return calls


@pytest.fixture
def fake_popen(monkeypatch: pytest.MonkeyPatch):
    """Capture subprocess.Popen calls without spawning anything."""
    captured: dict = {}

    class FakeProc:
        pid = 4242

    def fake_popen(args, **kwargs):
        captured["args"] = list(args)
        captured["kwargs"] = kwargs
        return FakeProc()

    monkeypatch.setattr(
        "android_cli_mac_x86_community.tools.emulator.subprocess.Popen",
        fake_popen,
    )
    return captured


def test_list_avd_invokes_emulator_with_list_avds_flag(fake_sdk, captured_run):
    emulator.list_avd()
    name, args, _ = captured_run[0]
    assert name == "emulator"
    assert args == ["-list-avds"]


def test_start_detached_passes_avd_name(fake_sdk, fake_popen):
    pid = emulator.start_detached("pixel7")
    assert pid == 4242

    args = fake_popen["args"]
    assert Path(args[0]).name == "emulator"
    assert "-avd" in args
    avd_idx = args.index("-avd")
    assert args[avd_idx + 1] == "pixel7"


def test_start_detached_appends_extra_args(fake_sdk, fake_popen):
    emulator.start_detached(
        "pixel7", extra_args=["-no-snapshot", "-netdelay", "none"]
    )
    args = fake_popen["args"]
    assert args[-3:] == ["-no-snapshot", "-netdelay", "none"]


def test_start_detached_uses_new_session_for_background(fake_sdk, fake_popen):
    emulator.start_detached("pixel7")
    kwargs = fake_popen["kwargs"]
    assert kwargs.get("start_new_session") is True
