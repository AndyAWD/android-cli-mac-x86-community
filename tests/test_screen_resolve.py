from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from android_cli_mac_x86_community.cli import app


SAMPLE_XML = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node class="android.widget.FrameLayout" bounds="[0,0][1080,1920]">
    <node class="android.widget.Button" resource-id="id/submit"
          text="OK" bounds="[100,200][300,260]"/>
    <node class="android.widget.Button" resource-id="id/cancel"
          text="Cancel" bounds="[400,200][600,260]"/>
  </node>
</hierarchy>
"""


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def stub_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    # Avoid hitting adb/uiautomator from the resolve command path.
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.screen.capture_layout_xml",
        lambda serial=None: SAMPLE_XML,
    )


def test_resolve_by_text_outputs_parsed_bounds(runner: CliRunner):
    result = runner.invoke(app, ["screen", "resolve", "--text", "OK"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert len(payload) == 1
    node = payload[0]
    assert node["resource-id"] == "id/submit"
    assert node["bounds"] == {
        "x1": 100, "y1": 200, "x2": 300, "y2": 260,
        "cx": 200, "cy": 230,
    }


def test_resolve_no_match_exits_one(runner: CliRunner):
    result = runner.invoke(app, ["screen", "resolve", "--text", "Nope"])
    assert result.exit_code == 1
    assert json.loads(result.stdout) == []


def test_resolve_requires_a_selector(runner: CliRunner):
    result = runner.invoke(app, ["screen", "resolve"])
    assert result.exit_code == 2
    assert "at least one" in result.stderr or "at least one" in result.output


def test_resolve_by_class_returns_multiple(runner: CliRunner):
    result = runner.invoke(
        app, ["screen", "resolve", "--class", "android.widget.Button"]
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert {n["resource-id"] for n in payload} == {"id/submit", "id/cancel"}
