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
        "version": "0.7.15232955",
        "launcher_version": "0.7.15232955",
        "sdk": "/Users/test/Library/Android/sdk",
    }
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.info._gather", lambda: sample
    )
    return sample


def test_info_default_prints_all_fields(runner: CliRunner):
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0, result.output
    assert "version: 0.7.15232955" in result.output
    assert "launcher_version: 0.7.15232955" in result.output
    assert "sdk: /Users/test/Library/Android/sdk" in result.output


def test_info_field_filter(runner: CliRunner):
    result = runner.invoke(app, ["info", "sdk"])
    assert result.exit_code == 0, result.output
    assert "/Users/test/Library/Android/sdk" in result.output
    assert "version:" not in result.output


def test_info_unknown_field_exits_with_error(runner: CliRunner):
    result = runner.invoke(app, ["info", "no_such_field"])
    assert result.exit_code == 2
    out = result.output + (result.stderr or "")
    assert "unknown field" in out
