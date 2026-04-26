"""`run` — install APKs and launch the entry activity."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from ..tools import adb


def run_cmd(
    apks: list[Path] = typer.Option(..., "--apks", help="APK file(s) to install"),
    activity: Optional[str] = typer.Option(None, "--activity",
        help="Component to launch, e.g. com.example/.MainActivity"),
    device: Optional[str] = typer.Option(None, "--device",
        help="Target device serial number"),
    type_: str = typer.Option("ACTIVITY", "--type",
        help="Component type (ACTIVITY, SERVICE, etc.)"),
    debug: bool = typer.Option(False, "--debug", help="Wait for debugger on launch"),
) -> None:
    """Deploy an Android Application."""
    for apk in apks:
        if not apk.exists():
            typer.echo(f"APK not found: {apk}", err=True)
            raise typer.Exit(2)

    install_result = adb.install(list(apks), serial=device)
    if install_result.stdout:
        typer.echo(install_result.stdout, nl=False)
    if not install_result.ok:
        typer.echo(install_result.stderr, err=True, nl=False)
        raise typer.Exit(install_result.returncode)

    if activity:
        if type_.upper() != "ACTIVITY":
            typer.echo(
                f"Note: --type={type_} is not yet implemented; only ACTIVITY launches.",
                err=True,
            )
        launch = adb.start_activity(activity, serial=device, debug=debug)
        if launch.stdout:
            typer.echo(launch.stdout, nl=False)
        if not launch.ok:
            typer.echo(launch.stderr, err=True, nl=False)
            raise typer.Exit(launch.returncode)
