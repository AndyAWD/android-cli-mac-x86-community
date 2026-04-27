from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from android_cli_mac_x86_community.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def stub_gradle_wrapper(monkeypatch: pytest.MonkeyPatch) -> None:
    # Avoid invoking the real gradle binary during tests.
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.create._run_gradle_wrapper",
        lambda target: None,
    )


def test_create_scaffolds_empty_compose_into_tmp(
    runner: CliRunner, tmp_path: Path
):
    target = tmp_path / "MyApp"
    result = runner.invoke(
        app,
        [
            "create", str(target),
            "--name", "MyApp",
            "--package", "com.example.myapp",
        ],
    )
    assert result.exit_code == 0, result.output

    # Top-level files
    assert (target / "settings.gradle.kts").exists()
    assert (target / "build.gradle.kts").exists()
    assert (target / "gradle.properties").exists()
    assert (target / ".gitignore").exists()

    # App module
    manifest = target / "app" / "src" / "main" / "AndroidManifest.xml"
    assert manifest.exists()
    assert "@style/Theme.MyApp" in manifest.read_text(encoding="utf-8")

    # Source under the rendered package path
    main = (target / "app" / "src" / "main" / "java"
            / "com" / "example" / "myapp" / "MainActivity.kt")
    assert main.exists()
    text = main.read_text(encoding="utf-8")
    assert "package com.example.myapp" in text
    assert 'Greeting("MyApp")' in text

    # rootProject.name in settings
    assert 'rootProject.name = "MyApp"' in (
        target / "settings.gradle.kts"
    ).read_text(encoding="utf-8")


def test_create_rejects_invalid_package(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "create", str(tmp_path / "X"),
            "--name", "X",
            "--package", "NotAPackage",
        ],
    )
    assert result.exit_code != 0
    assert "invalid package" in result.output or "invalid package" in result.stderr


def test_create_refuses_non_empty_target(runner: CliRunner, tmp_path: Path):
    target = tmp_path / "existing"
    target.mkdir()
    (target / "leftover").write_text("data", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "create", str(target),
            "--name", "X",
            "--package", "com.example.x",
        ],
    )
    assert result.exit_code == 1
    assert "not empty" in result.output or "not empty" in result.stderr


def test_create_unknown_template_lists_available(
    runner: CliRunner, tmp_path: Path
):
    result = runner.invoke(
        app,
        [
            "create", str(tmp_path / "Y"),
            "--name", "Y",
            "--package", "com.example.y",
            "--template", "no_such_template",
        ],
    )
    assert result.exit_code == 2
    out = result.output + (result.stderr or "")
    assert "empty_compose" in out
