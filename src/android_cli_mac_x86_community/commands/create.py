"""`create` — scaffold a new Android project from a built-in template."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import typer

from ..utils.scaffold import TargetNotEmptyError, scaffold


_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_PACKAGE_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")


def _validate_package(package: str) -> None:
    if not _PACKAGE_RE.fullmatch(package):
        raise typer.BadParameter(
            f"invalid package '{package}'; expected reverse-domain like "
            "com.example.myapp (lowercase, at least two segments)"
        )


_WRAPPER_GRADLE_VERSION = "8.7"


def _run_gradle_wrapper(target: Path) -> None:
    if shutil.which("gradle") is None:
        typer.echo(
            "warning: 'gradle' not found in PATH; skipping wrapper generation. "
            "Install Gradle and run `gradle wrapper` inside the new project to "
            "create gradlew / gradlew.bat.",
            err=True,
        )
        return
    result = subprocess.run(
        [
            "gradle", "wrapper",
            "--gradle-version", _WRAPPER_GRADLE_VERSION,
            "--distribution-type", "bin",
        ],
        cwd=target, capture_output=True, text=True,
    )
    if result.returncode != 0:
        typer.echo(result.stderr, err=True, nl=False)
        raise typer.Exit(result.returncode)


def _available_templates() -> list[str]:
    return sorted(p.name for p in _TEMPLATES_DIR.iterdir() if p.is_dir())


def create_cmd(
    path: Optional[Path] = typer.Argument(None,
        help="Directory to scaffold the project into"),
    name: Optional[str] = typer.Option(None, "--name",
        help="App display name, e.g. 'My App'"),
    package: Optional[str] = typer.Option(None, "--package",
        help="Android package, e.g. com.example.myapp"),
    template: str = typer.Option("empty_compose", "--template",
        help="Template to use"),
    list_templates: bool = typer.Option(False, "--list-templates",
        help="List available templates and exit"),
    no_wrapper: bool = typer.Option(False, "--no-wrapper",
        help="Skip running `gradle wrapper` after scaffolding"),
) -> None:
    """Scaffold a new Android project."""
    if list_templates:
        for t in _available_templates():
            typer.echo(t)
        return

    if path is None or name is None or package is None:
        typer.echo(
            "error: PATH, --name, and --package are required (or pass --list-templates)",
            err=True,
        )
        raise typer.Exit(2)

    _validate_package(package)

    template_root = _TEMPLATES_DIR / template
    if not template_root.is_dir():
        typer.echo(
            f"error: template '{template}' not found. available: "
            f"{', '.join(_available_templates())}",
            err=True,
        )
        raise typer.Exit(2)

    target = path.resolve()
    vars = {
        "app_name": name,
        "package": package,
        "package_path": package.replace(".", "/"),
    }
    try:
        created = scaffold(template_root, target, vars)
    except TargetNotEmptyError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1)

    typer.echo(f"created {len(created)} files in {target}")

    if not no_wrapper:
        _run_gradle_wrapper(target)
