from __future__ import annotations

from pathlib import Path

import pytest

from android_cli_mac_x86_community.tools import sdkmanager


@pytest.fixture
def captured_run(monkeypatch: pytest.MonkeyPatch):
    from android_cli_mac_x86_community.tools import _subprocess

    calls: list[tuple] = []

    def fake_run(executable, args, **kwargs):
        calls.append((Path(executable).name, list(args), kwargs))
        return _subprocess.ToolResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("android_cli_mac_x86_community.tools.sdkmanager.run", fake_run)
    return calls


def test_list_passes_dash_dash_list(fake_sdk, captured_run):
    sdkmanager.list_packages()
    name, args, _ = captured_run[0]
    assert name == "sdkmanager"
    assert args == ["--list"]


def test_install_forwards_packages_and_accepts_license(fake_sdk, captured_run):
    sdkmanager.install(["platform-tools", "platforms;android-34"])
    name, args, kwargs = captured_run[0]
    assert name == "sdkmanager"
    assert args == ["platform-tools", "platforms;android-34"]
    assert kwargs.get("input_text") == "y\n"


def test_install_rejects_empty(fake_sdk):
    with pytest.raises(ValueError):
        sdkmanager.install([])


def test_remove_uses_uninstall_flag(fake_sdk, captured_run):
    sdkmanager.remove(["platforms;android-30"])
    _, args, _ = captured_run[0]
    assert args == ["--uninstall", "platforms;android-30"]
