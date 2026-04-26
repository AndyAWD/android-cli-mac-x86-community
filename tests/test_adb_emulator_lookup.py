from __future__ import annotations

from pathlib import Path

import pytest

from android_cli_mac_x86_community.tools import adb
from android_cli_mac_x86_community.tools._subprocess import ToolResult


@pytest.fixture
def fake_run(monkeypatch: pytest.MonkeyPatch):
    queue: list[ToolResult] = []
    calls: list[tuple] = []

    def fake(executable, args, **kwargs):
        calls.append((Path(executable).name, list(args)))
        return queue.pop(0)

    monkeypatch.setattr("android_cli_mac_x86_community.tools.adb.run", fake)
    return queue, calls


def test_list_emulator_serials_filters_non_emulators(fake_sdk, fake_run):
    queue, _ = fake_run
    queue.append(ToolResult(0, stdout=(
        "List of devices attached\n"
        "emulator-5554       device product:sdk_phone\n"
        "ABCDEF1234          device product:real_phone\n"
        "emulator-5556       device\n"
    ), stderr=""))
    assert adb.list_emulator_serials() == ["emulator-5554", "emulator-5556"]


def test_emu_avd_name_returns_first_line(fake_sdk, fake_run):
    queue, _ = fake_run
    queue.append(ToolResult(0, stdout="pixel7\nOK\n", stderr=""))
    assert adb.emu_avd_name("emulator-5554") == "pixel7"


def test_emu_avd_name_failure_returns_empty(fake_sdk, fake_run):
    queue, _ = fake_run
    queue.append(ToolResult(1, stdout="", stderr="device offline"))
    assert adb.emu_avd_name("emulator-5554") == ""


def test_find_emulator_serial_by_avd_matches(fake_sdk, fake_run):
    queue, _ = fake_run
    queue.append(ToolResult(0, stdout=(
        "List of devices attached\n"
        "emulator-5554       device\n"
        "emulator-5556       device\n"
    ), stderr=""))
    queue.append(ToolResult(0, stdout="other\nOK\n", stderr=""))
    queue.append(ToolResult(0, stdout="pixel7\nOK\n", stderr=""))
    assert adb.find_emulator_serial_by_avd("pixel7") == "emulator-5556"


def test_find_emulator_serial_by_avd_no_match(fake_sdk, fake_run):
    queue, _ = fake_run
    queue.append(ToolResult(0, stdout=(
        "List of devices attached\n"
        "emulator-5554       device\n"
    ), stderr=""))
    queue.append(ToolResult(0, stdout="other\nOK\n", stderr=""))
    assert adb.find_emulator_serial_by_avd("pixel7") is None
