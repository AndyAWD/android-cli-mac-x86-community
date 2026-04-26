from __future__ import annotations

from pathlib import Path

import pytest

from android_cli_mac_x86_community.tools import avdmanager


@pytest.fixture
def captured_run(monkeypatch: pytest.MonkeyPatch):
    from android_cli_mac_x86_community.tools import _subprocess

    calls: list[tuple] = []

    def fake_run(executable, args, **kwargs):
        calls.append((Path(executable).name, list(args), kwargs))
        return _subprocess.ToolResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("android_cli_mac_x86_community.tools.avdmanager.run", fake_run)
    return calls


def test_list_avd(fake_sdk, captured_run):
    avdmanager.list_avd()
    name, args, _ = captured_run[0]
    assert name == "avdmanager"
    assert args == ["list", "avd"]


def test_create_basic(fake_sdk, captured_run):
    avdmanager.create("pixel7", "system-images;android-34;google_apis;x86_64")
    _, args, kwargs = captured_run[0]
    assert args[:2] == ["create", "avd"]
    assert "--name" in args and "pixel7" in args
    assert "--package" in args
    assert kwargs.get("input_text") == "no\n"


def test_create_with_device_and_force(fake_sdk, captured_run):
    avdmanager.create("p", "img", device="pixel_7", force=True)
    _, args, _ = captured_run[0]
    assert "--device" in args and "pixel_7" in args
    assert "--force" in args


def test_delete(fake_sdk, captured_run):
    avdmanager.delete("p")
    _, args, _ = captured_run[0]
    assert args == ["delete", "avd", "--name", "p"]
