from __future__ import annotations

import pytest
from typer.testing import CliRunner

from android_cli_mac_x86_community.cli import app
from android_cli_mac_x86_community.tools._subprocess import ToolResult


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def captured_calls(monkeypatch: pytest.MonkeyPatch):
    calls: list[tuple] = []

    def fake_list_packages():
        calls.append(("list_packages", ()))
        return ToolResult(returncode=0, stdout="package list\n", stderr="")

    def fake_install(packages):
        calls.append(("install", tuple(packages)))
        return ToolResult(returncode=0, stdout="installed\n", stderr="")

    def fake_update_all():
        calls.append(("update_all", ()))
        return ToolResult(returncode=0, stdout="updated\n", stderr="")

    def fake_remove(packages):
        calls.append(("remove", tuple(packages)))
        return ToolResult(returncode=0, stdout="removed\n", stderr="")

    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.sdk.sdkmanager.list_packages",
        fake_list_packages,
    )
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.sdk.sdkmanager.install",
        fake_install,
    )
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.sdk.sdkmanager.update_all",
        fake_update_all,
    )
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.sdk.sdkmanager.remove",
        fake_remove,
    )
    return calls


def test_sdk_list_invokes_list_packages(runner: CliRunner, captured_calls):
    result = runner.invoke(app, ["sdk", "list"])
    assert result.exit_code == 0, result.output
    assert "package list" in result.output
    assert captured_calls[0] == ("list_packages", ())


def test_sdk_install_passes_packages(runner: CliRunner, captured_calls):
    result = runner.invoke(
        app, ["sdk", "install", "platform-tools", "platforms;android-34"]
    )
    assert result.exit_code == 0, result.output
    assert captured_calls[0] == (
        "install",
        ("platform-tools", "platforms;android-34"),
    )


def test_sdk_update_invokes_update_all(runner: CliRunner, captured_calls):
    result = runner.invoke(app, ["sdk", "update"])
    assert result.exit_code == 0, result.output
    assert captured_calls[0] == ("update_all", ())


def test_sdk_remove_passes_packages(runner: CliRunner, captured_calls):
    result = runner.invoke(app, ["sdk", "remove", "platforms;android-30"])
    assert result.exit_code == 0, result.output
    assert captured_calls[0] == ("remove", ("platforms;android-30",))


def test_sdk_install_propagates_failure_exit_code(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.sdk.sdkmanager.install",
        lambda packages: ToolResult(
            returncode=7, stdout="", stderr="boom\n"
        ),
    )
    result = runner.invoke(app, ["sdk", "install", "x"])
    assert result.exit_code == 7
