"""`info` — print SDK location and tool versions."""
from __future__ import annotations

from typing import Optional

import typer

from ..utils.android_home import SdkNotFoundError, find_sdk_root


def _gather() -> dict:
    data: dict = {
        "version": "0.7.15232955",
        "launcher_version": "0.7.15232955",
    }
    try:
        sdk_root = find_sdk_root()
        data["sdk"] = str(sdk_root)
    except SdkNotFoundError as exc:
        data["sdk"] = ""
    return data


def info_cmd(
    field: Optional[str] = typer.Argument(None, help="Specific field to print"),
) -> None:
    """Print environment information (SDK Location, etc.)."""
    data = _gather()

    if field:
        value = data.get(field)
        if value is None and field not in data:
            typer.echo(f"unknown field: {field}", err=True)
            raise typer.Exit(2)
        typer.echo(value)
        return

    # To match official CLI exactly, order is sdk, version, launcher_version
    if "sdk" in data:
        typer.echo(f"sdk: {data['sdk']}")
    typer.echo(f"version: {data['version']}")
    typer.echo(f"launcher_version: {data['launcher_version']}")
