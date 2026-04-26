from __future__ import annotations

from pathlib import Path

from android_cli_mac_x86_community.commands.describe import _scan_apks


def test_scan_apks_finds_module_and_variant(tmp_path: Path):
    apk = tmp_path / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    apk.parent.mkdir(parents=True)
    apk.write_bytes(b"")

    results = _scan_apks(tmp_path)
    assert len(results) == 1
    assert results[0]["module"] == "app"
    assert results[0]["variant"] == "debug"
    assert results[0]["path"].endswith("app-debug.apk")


def test_scan_apks_handles_multi_module(tmp_path: Path):
    for module, variant in [("app", "debug"), ("app", "release"),
                            ("library", "debug")]:
        apk = (tmp_path / module / "build" / "outputs" / "apk"
               / variant / f"{module}-{variant}.apk")
        apk.parent.mkdir(parents=True)
        apk.write_bytes(b"")

    results = _scan_apks(tmp_path)
    assert len(results) == 3
    modules = {r["module"] for r in results}
    assert modules == {"app", "library"}
    variants = {r["variant"] for r in results}
    assert variants == {"debug", "release"}


def test_scan_apks_empty_project(tmp_path: Path):
    assert _scan_apks(tmp_path) == []
