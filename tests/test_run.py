from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from android_cli_mac_x86_community.cli import app
from android_cli_mac_x86_community.tools._subprocess import ToolResult


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def fake_apk(tmp_path: Path) -> Path:
    apk = tmp_path / "app-debug.apk"
    apk.write_bytes(b"fake apk")
    return apk


@pytest.fixture
def captured_run(monkeypatch: pytest.MonkeyPatch):
    captured: dict = {"install": [], "start": []}

    def fake_install(apks, *, serial=None):
        captured["install"].append({"apks": list(apks), "serial": serial})
        return ToolResult(returncode=0, stdout="Success\n", stderr="")

    def fake_start(component, *, serial=None, debug=False):
        captured["start"].append(
            {"component": component, "serial": serial, "debug": debug}
        )
        return ToolResult(returncode=0, stdout="Started\n", stderr="")

    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.run.adb.install",
        fake_install,
    )
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.run.adb.start_activity",
        fake_start,
    )
    return captured


def test_run_installs_apk(runner: CliRunner, fake_apk: Path, captured_run):
    result = runner.invoke(app, ["run", "--apks", str(fake_apk)])
    assert result.exit_code == 0, result.output
    assert len(captured_run["install"]) == 1
    assert captured_run["install"][0]["apks"] == [fake_apk]
    assert captured_run["start"] == []


def test_run_with_activity_launches_after_install(
    runner: CliRunner, fake_apk: Path, captured_run
):
    result = runner.invoke(
        app,
        [
            "run",
            "--apks", str(fake_apk),
            "--activity", "com.example/.MainActivity",
            "--device", "emulator-5554",
            "--debug",
        ],
    )
    assert result.exit_code == 0, result.output
    assert captured_run["install"][0]["serial"] == "emulator-5554"
    assert captured_run["start"][0] == {
        "component": "com.example/.MainActivity",
        "serial": "emulator-5554",
        "debug": True,
    }


def test_run_missing_apk_exits_2(runner: CliRunner, tmp_path: Path):
    missing = tmp_path / "no-such.apk"
    result = runner.invoke(app, ["run", "--apks", str(missing)])
    assert result.exit_code == 2
    out = result.output + (result.stderr or "")
    assert "APK not found" in out


def test_run_propagates_install_failure(
    runner: CliRunner, fake_apk: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.run.adb.install",
        lambda apks, *, serial=None: ToolResult(
            returncode=5, stdout="", stderr="install fail\n"
        ),
    )
    result = runner.invoke(app, ["run", "--apks", str(fake_apk)])
    assert result.exit_code == 5


def test_run_warns_on_unsupported_type(
    runner: CliRunner, fake_apk: Path, captured_run
):
    result = runner.invoke(
        app,
        [
            "run",
            "--apks", str(fake_apk),
            "--activity", "com.example/.Foo",
            "--type", "SERVICE",
        ],
    )
    assert result.exit_code == 0, result.output
    out = result.output + (result.stderr or "")
    assert "SERVICE" in out
    # Activity launch still happens (current behavior).
    assert len(captured_run["start"]) == 1
