"""`init` — create the user-level config directory tree."""
from __future__ import annotations

import typer

from ..utils.config import config_file, config_root, ensure_layout, skills_dir


def init_cmd() -> None:
    """Initialize the local config directory at ~/.android-cli-mac-x86-community/."""
    root = ensure_layout()
    typer.echo(f"config root: {root}")
    typer.echo(f"skills dir:  {skills_dir()}")
    typer.echo(f"config file: {config_file()}")
