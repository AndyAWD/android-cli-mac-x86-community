from __future__ import annotations

import pytest
from typer.testing import CliRunner

from android_cli_mac_x86_community.cli import app
from android_cli_mac_x86_community.tools._subprocess import ToolResult


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _ok(stdout: str = "") -> ToolResult:
    return ToolResult(returncode=0, stdout=stdout, stderr="")


def test_emulator_list_dispatches_to_emu_tool(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    captured: list[str] = []

    def fake_list():
        captured.append("called")
        return _ok("Pixel_7\nPixel_6\n")

    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.emulator.emu_tool.list_avd",
        fake_list,
    )
    result = runner.invoke(app, ["emulator", "list"])
    assert result.exit_code == 0, result.output
    assert "Pixel_7" in result.output
    assert captured == ["called"]


def test_emulator_create_passes_options_to_avdmanager(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    captured: dict = {}

    def fake_create(name, image, *, device=None, force=False):
        captured.update(
            name=name, image=image, device=device, force=force
        )
        return _ok()

    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.emulator.avdmanager.create",
        fake_create,
    )
    result = runner.invoke(
        app,
        [
            "emulator", "create",
            "--name", "pixel7",
            "--image", "system-images;android-34;google_apis;x86_64",
            "--device", "pixel_7",
            "--force",
        ],
    )
    assert result.exit_code == 0, result.output
    assert captured == {
        "name": "pixel7",
        "image": "system-images;android-34;google_apis;x86_64",
        "device": "pixel_7",
        "force": True,
    }
    assert "Created AVD: pixel7" in result.output


def test_emulator_start_invokes_start_detached(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    captured: list[str] = []

    def fake_start(name):
        captured.append(name)
        return 4242

    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.emulator.emu_tool.start_detached",
        fake_start,
    )
    result = runner.invoke(app, ["emulator", "start", "--name", "pixel7"])
    assert result.exit_code == 0, result.output
    assert captured == ["pixel7"]
    assert "pixel7" in result.output
    assert "4242" in result.output


def test_emulator_stop_when_not_running_returns_error(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.emulator.adb.find_emulator_serial_by_avd",
        lambda name: None,
    )
    result = runner.invoke(app, ["emulator", "stop", "--name", "pixel7"])
    assert result.exit_code == 1
    out = result.output + (result.stderr or "")
    assert "No running emulator" in out


def test_emulator_stop_running_avd_kills_serial(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    killed: list[str] = []

    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.emulator.adb.find_emulator_serial_by_avd",
        lambda name: "emulator-5554",
    )

    def fake_kill(serial):
        killed.append(serial)
        return _ok()

    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.emulator.adb.emu_kill",
        fake_kill,
    )
    result = runner.invoke(app, ["emulator", "stop", "--name", "pixel7"])
    assert result.exit_code == 0, result.output
    assert killed == ["emulator-5554"]


def test_emulator_remove_passes_name_to_avdmanager(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    captured: list[str] = []

    def fake_delete(name):
        captured.append(name)
        return _ok()

    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.emulator.avdmanager.delete",
        fake_delete,
    )
    result = runner.invoke(app, ["emulator", "remove", "--name", "pixel7"])
    assert result.exit_code == 0, result.output
    assert captured == ["pixel7"]
    assert "Deleted AVD: pixel7" in result.output
