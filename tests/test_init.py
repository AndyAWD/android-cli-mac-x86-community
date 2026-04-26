from __future__ import annotations

from pathlib import Path

import pytest

from android_cli_mac_x86_community.utils.config import (
    config_file,
    config_root,
    ensure_layout,
    skills_dir,
)


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    return tmp_path


def test_ensure_layout_creates_dirs(fake_home: Path):
    ensure_layout()
    assert config_root().is_dir()
    assert skills_dir().is_dir()
    assert config_file().exists()


def test_ensure_layout_is_idempotent(fake_home: Path):
    ensure_layout()
    config_file().write_text("# user customized\n", encoding="utf-8")
    ensure_layout()
    assert config_file().read_text(encoding="utf-8") == "# user customized\n"
