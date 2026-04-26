"""`info` — print SDK location and tool versions."""
from __future__ import annotations

import json
import os
import platform
import shutil
from typing import Optional

import typer

from ..tools import adb
from ..tools._subprocess import ToolNotFoundError
from ..utils.android_home import SdkNotFoundError, find_sdk_root


def _gather() -> dict:
    data: dict = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }
    try:
        sdk_root = find_sdk_root()
        data["sdk_location"] = str(sdk_root)
    except SdkNotFoundError as exc:
        data["sdk_location"] = None
        data["sdk_error"] = str(exc)

    try:
        result = adb.version()
        first_line = result.stdout.splitlines()[0] if result.stdout else ""
        data["adb_version"] = first_line
    except (ToolNotFoundError, FileNotFoundError):
        data["adb_version"] = None

    java_home = os.environ.get("JAVA_HOME")
    data["java_home"] = java_home
    java = shutil.which("java")
    data["java_executable"] = java
    return data


def info_cmd(
    field: Optional[str] = typer.Argument(None, help="Specific field to print"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    """Print environment information (SDK Location, etc.)."""
    data = _gather()

    if field:
        value = data.get(field)
        if value is None and field not in data:
            typer.echo(f"unknown field: {field}", err=True)
            raise typer.Exit(2)
        typer.echo(value if not json_output else json.dumps(value))
        return

    if json_output:
        typer.echo(json.dumps(data, indent=2))
        return

    width = max(len(k) for k in data)
    for key, value in data.items():
        typer.echo(f"{key.ljust(width)}  {value}")
