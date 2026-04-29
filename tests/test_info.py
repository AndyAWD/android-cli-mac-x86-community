from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from android_cli_mac_x86_community.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def stub_gather(monkeypatch: pytest.MonkeyPatch):
    sample = {
        "platform": "Darwin-23.6.0",
        "machine": "x86_64",
        "python": "3.11.9",
        "sdk_location": "/Users/test/Library/Android/sdk",
        "adb_version": "Android Debug Bridge version 1.0.41",
        "java_home": "/opt/homebrew/openjdk@17",
        "java_executable": "/usr/bin/java",
    }
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.info._gather", lambda: sample
    )
    return sample


def test_info_default_prints_all_fields(runner: CliRunner):
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0, result.output
    assert "platform" in result.output
    assert "sdk_location" in result.output
    assert "/Users/test/Library/Android/sdk" in result.output


def test_info_json_emits_valid_json(runner: CliRunner):
    result = runner.invoke(app, ["info", "--json"])
    assert result.exit_code == 0, result.output
    parsed = json.loads(result.output)
    assert parsed["sdk_location"] == "/Users/test/Library/Android/sdk"


def test_info_field_filter(runner: CliRunner):
    result = runner.invoke(app, ["info", "sdk_location"])
    assert result.exit_code == 0, result.output
    assert "/Users/test/Library/Android/sdk" in result.output
    # Only the field value should be printed, not the full table.
    assert "platform" not in result.output


def test_info_unknown_field_exits_with_error(runner: CliRunner):
    result = runner.invoke(app, ["info", "no_such_field"])
    assert result.exit_code == 2
    out = result.output + (result.stderr or "")
    assert "unknown field" in out
