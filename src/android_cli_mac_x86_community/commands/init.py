"""`init` — create the user-level config directory tree."""
from __future__ import annotations

import os
import shutil

import typer

from ..utils.android_home import SdkNotFoundError, find_sdk_root
from ..utils.config import config_file, config_root, ensure_layout, skills_dir


def init_cmd() -> None:
    """Initialize the local config directory at ~/.android-cli-mac-x86-community/."""
    root = ensure_layout()
    typer.echo(f"config root: {root}")
    typer.echo(f"skills dir:  {skills_dir()}")
    typer.echo(f"config file: {config_file()}")

    typer.echo("")
    typer.echo("environment check:")
    _check_environment()


def _check_environment() -> None:
    if os.environ.get("ANDROID_HOME"):
        typer.echo(f"  ANDROID_HOME: {os.environ['ANDROID_HOME']}")
    else:
        typer.echo(
            "  ANDROID_HOME: not set "
            "(needed by ./gradlew assembleDebug; "
            "export ANDROID_HOME=$HOME/Library/Android/sdk)"
        )

    try:
        sdk_root = find_sdk_root()
        typer.echo(f"  sdk_root:     {sdk_root}")
    except SdkNotFoundError as exc:
        typer.echo(f"  sdk_root:     not found ({exc})")

    gradle = shutil.which("gradle")
    if gradle:
        typer.echo(f"  gradle:       {gradle}")
    else:
        typer.echo(
            "  gradle:       not found "
            "(needed by `create` to generate gradle wrapper; "
            "install with `brew install gradle`)"
        )
