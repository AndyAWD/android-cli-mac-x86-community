"""Locations for this CLI's per-user state under ~/.android-cli-mac-x86-community/."""
from __future__ import annotations

from pathlib import Path

CONFIG_DIRNAME = ".android-cli-mac-x86-community"


def config_root() -> Path:
    return Path.home() / CONFIG_DIRNAME


def skills_dir() -> Path:
    return config_root() / "skills"


def layout_snapshot_path() -> Path:
    return config_root() / "last_layout.xml"


def config_file() -> Path:
    return config_root() / "config.toml"


DEFAULT_CONFIG_TOML = """# android-cli-mac-x86-community user configuration

[skills]
# Upstream repo for `skills list` / `skills add` (Apache-2.0).
upstream = "android/skills"
"""


def ensure_layout(*, write_default_config: bool = True) -> Path:
    """Create the config directory tree if missing. Idempotent. Returns root."""
    root = config_root()
    root.mkdir(parents=True, exist_ok=True)
    skills_dir().mkdir(parents=True, exist_ok=True)
    if write_default_config and not config_file().exists():
        config_file().write_text(DEFAULT_CONFIG_TOML, encoding="utf-8")
    return root
