from __future__ import annotations

from pathlib import Path

import pytest

from android_cli_mac_x86_community.utils.scaffold import (
    TargetNotEmptyError,
    render,
    scaffold,
)


def test_render_replaces_double_brace_tokens():
    assert render("hi {{name}} from {{place}}", {"name": "A", "place": "B"}) \
        == "hi A from B"


def test_render_leaves_unknown_tokens_intact():
    assert render("hello {{stranger}}", {"name": "A"}) == "hello {{stranger}}"


def _make_template(root: Path) -> None:
    (root / "settings.kts.tmpl").write_text(
        'rootProject.name = "{{app_name}}"\n', encoding="utf-8")
    pkg_dir = root / "app" / "java" / "{{package_path}}"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "Main.kt.tmpl").write_text(
        "package {{package}}\nclass Main\n", encoding="utf-8")
    (root / "_gitignore.tmpl").write_text("/build\n", encoding="utf-8")


def test_scaffold_writes_rendered_files_and_paths(tmp_path: Path):
    template = tmp_path / "tpl"
    template.mkdir()
    _make_template(template)

    target = tmp_path / "out"
    created = scaffold(template, target, {
        "app_name": "Demo",
        "package": "com.example.demo",
        "package_path": "com/example/demo",
    })

    assert (target / "settings.kts").read_text(encoding="utf-8") \
        == 'rootProject.name = "Demo"\n'
    main = target / "app" / "java" / "com" / "example" / "demo" / "Main.kt"
    assert main.exists()
    assert "package com.example.demo" in main.read_text(encoding="utf-8")
    # _gitignore is rewritten to .gitignore at the destination
    assert (target / ".gitignore").read_text(encoding="utf-8") == "/build\n"
    assert {p.as_posix() for p in created} == {
        "settings.kts",
        "app/java/com/example/demo/Main.kt",
        ".gitignore",
    }


def test_scaffold_refuses_non_empty_target(tmp_path: Path):
    template = tmp_path / "tpl"
    template.mkdir()
    (template / "x.tmpl").write_text("ok", encoding="utf-8")

    target = tmp_path / "out"
    target.mkdir()
    (target / "leftover").write_text("data", encoding="utf-8")

    with pytest.raises(TargetNotEmptyError):
        scaffold(template, target, {})


def test_scaffold_into_missing_target_creates_it(tmp_path: Path):
    template = tmp_path / "tpl"
    template.mkdir()
    (template / "hello.tmpl").write_text("hi", encoding="utf-8")

    target = tmp_path / "deep" / "new" / "out"
    scaffold(template, target, {})
    assert (target / "hello").read_text(encoding="utf-8") == "hi"


def test_scaffold_skips_non_tmpl_files(tmp_path: Path):
    template = tmp_path / "tpl"
    template.mkdir()
    (template / "kept.tmpl").write_text("ok", encoding="utf-8")
    (template / "ignored.txt").write_text("nope", encoding="utf-8")

    target = tmp_path / "out"
    scaffold(template, target, {})

    assert (target / "kept").exists()
    assert not (target / "ignored.txt").exists()
    assert not (target / "ignored").exists()
