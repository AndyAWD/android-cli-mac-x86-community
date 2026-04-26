"""`describe` — emit JSON describing an Android project's build outputs."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer

from ..tools._subprocess import run


def _find_gradlew(project_dir: Path) -> Path | None:
    candidate = project_dir / ("gradlew.bat" if os.name == "nt" else "gradlew")
    return candidate if candidate.exists() else None


def _scan_apks(project_dir: Path) -> list[dict]:
    """Walk app/build/outputs/apk/** and module-level build/outputs/apk/**."""
    apks: list[dict] = []
    for outputs in project_dir.rglob("build/outputs/apk"):
        for apk in outputs.rglob("*.apk"):
            rel = apk.relative_to(project_dir)
            module = rel.parts[0] if len(rel.parts) > 1 else ""
            variant = apk.parent.name
            apks.append({
                "module": module,
                "variant": variant,
                "path": str(apk),
            })
    return apks


def _list_assemble_tasks(gradlew: Path, project_dir: Path) -> list[str]:
    """Return assemble* task names found by `gradlew tasks --all`."""
    result = run(gradlew, ["tasks", "--all"])
    if not result.ok:
        return []
    tasks: list[str] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("assemble") and " - " in line:
            name = line.split(" - ", 1)[0].strip()
            tasks.append(name)
        elif ":assemble" in line and " - " in line:
            name = line.split(" - ", 1)[0].strip()
            tasks.append(name)
    return tasks


def describe_cmd(
    project_dir: Path = typer.Option(Path("."), "--project_dir",
        help="Path to the Android project root"),
    pretty: bool = typer.Option(True, "--pretty/--no-pretty",
        help="Pretty-print the JSON output"),
) -> None:
    """Analyze an Android project and emit JSON metadata."""
    project_dir = project_dir.resolve()
    if not project_dir.is_dir():
        typer.echo(f"Not a directory: {project_dir}", err=True)
        raise typer.Exit(2)

    gradlew = _find_gradlew(project_dir)
    output: dict = {
        "project_dir": str(project_dir),
        "gradle_wrapper": str(gradlew) if gradlew else None,
        "build_targets": [],
        "apks": _scan_apks(project_dir),
    }

    if gradlew:
        output["build_targets"] = _list_assemble_tasks(gradlew, project_dir)
    else:
        output["warning"] = "No gradlew found; build_targets is empty."

    indent = 2 if pretty else None
    json.dump(output, sys.stdout, indent=indent, ensure_ascii=False)
    sys.stdout.write("\n")
