from __future__ import annotations

from pathlib import Path

import pytest

from android_cli_mac_x86_community.tools import _subprocess, adb
from android_cli_mac_x86_community.utils import uiautomator


@pytest.fixture
def captured_adb_run(monkeypatch: pytest.MonkeyPatch):
    calls: list[tuple] = []

    def fake_run(executable, args, **kwargs):
        calls.append((Path(executable).name, list(args), kwargs))
        return _subprocess.ToolResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("android_cli_mac_x86_community.tools.adb.run", fake_run)
    return calls


def test_uiautomator_dump_uses_data_local_tmp_by_default(
    fake_sdk, captured_adb_run
):
    adb.uiautomator_dump()
    _, args, _ = captured_adb_run[0]
    # shell <command>
    assert args[0] == "shell"
    assert args[1] == "uiautomator dump /data/local/tmp/window_dump.xml"


def test_uiautomator_dump_accepts_custom_remote_path(
    fake_sdk, captured_adb_run
):
    adb.uiautomator_dump(remote_path="/sdcard/foo.xml")
    _, args, _ = captured_adb_run[0]
    assert args[1] == "uiautomator dump /sdcard/foo.xml"


def test_capture_layout_xml_pulls_from_data_local_tmp(
    fake_sdk, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """capture_layout_xml() must pull from /data/local/tmp/, not /sdcard/."""
    pulled_xml = "<hierarchy/>"
    pull_calls: list[tuple] = []

    def fake_dump(*, serial=None, remote_path):
        return _subprocess.ToolResult(returncode=0, stdout="", stderr="")

    def fake_pull(remote, local, *, serial=None):
        pull_calls.append((remote, str(local), serial))
        Path(local).write_text(pulled_xml, encoding="utf-8")
        return _subprocess.ToolResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(
        "android_cli_mac_x86_community.utils.uiautomator.adb.uiautomator_dump",
        fake_dump,
    )
    monkeypatch.setattr(
        "android_cli_mac_x86_community.utils.uiautomator.adb.pull",
        fake_pull,
    )

    out = uiautomator.capture_layout_xml(serial="emulator-5554")
    assert out == pulled_xml
    assert len(pull_calls) == 1
    remote, _, serial = pull_calls[0]
    assert remote == "/data/local/tmp/window_dump.xml"
    assert serial == "emulator-5554"
