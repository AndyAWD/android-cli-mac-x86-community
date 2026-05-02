"""`create` — scaffold a new Android project from a built-in template."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import typer

from ..utils.android_home import SdkNotFoundError, find_sdk_root
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


def _run_gradle_wrapper(target: Path, gradle_version: str) -> None:
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
            "--gradle-version", gradle_version,
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
    gradle_version: str = typer.Option(
        _WRAPPER_GRADLE_VERSION, "--gradle-version",
        help=(
            f"Gradle wrapper version (default: {_WRAPPER_GRADLE_VERSION}, "
            "matched to AGP 8.5; bump only if you also bump AGP)."
        ),
    ),
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
    theme_name = re.sub(r"\W+", "", name) or "App"
    vars = {
        "app_name": name,
        "theme_name": theme_name,
        "package": package,
        "package_path": package.replace(".", "/"),
    }
    try:
        created = scaffold(template_root, target, vars)
    except TargetNotEmptyError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1)

    typer.echo(f"created {len(created)} files in {target}")

    _write_local_properties(target)

    if not no_wrapper:
        _run_gradle_wrapper(target, gradle_version)


def _write_local_properties(target: Path) -> None:
    """Write `local.properties` pointing at the detected SDK root.

    AGP reads `sdk.dir` from this file when ANDROID_HOME isn't set, so writing
    it removes one common cause of `./gradlew assembleDebug` failures on a
    freshly-scaffolded project.
    """
    try:
        sdk_root = find_sdk_root()
    except SdkNotFoundError:
        typer.echo(
            "warning: Android SDK not found; skipped writing local.properties. "
            "Set ANDROID_HOME before running ./gradlew assembleDebug.",
            err=True,
        )
        return
    sdk_dir = str(sdk_root).replace("\\", "\\\\").replace(":", "\\:")
    (target / "local.properties").write_text(
        f"sdk.dir={sdk_dir}\n", encoding="utf-8"
    )
