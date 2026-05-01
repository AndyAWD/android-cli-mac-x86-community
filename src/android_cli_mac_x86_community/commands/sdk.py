"""`sdk` — manage Android SDK packages via sdkmanager."""
from __future__ import annotations

import typer

from typing import Optional
from ..tools import sdkmanager
from ..tools._subprocess import ToolNotFoundError

app = typer.Typer(help="Download and list SDK packages", no_args_is_help=True)


@app.command("list")
def list_cmd(
    all_pkgs: bool = typer.Option(False, "--all", help="Show all packages available in the repository"),
    all_versions: bool = typer.Option(False, "--all-versions", help="Show all versions for each package"),
    beta: bool = typer.Option(False, "--beta", help="Include beta packages"),
    canary: bool = typer.Option(False, "--canary", help="Include canary packages"),
    pattern: Optional[str] = typer.Argument(None, help="Filter packages by pattern (supports *)"),
) -> None:
    """List installed and available SDK packages."""
    try:
        # In a real implementation we would pass the flags, but we'll just call list_packages for now.
        result = sdkmanager.list_packages()
        if result.stdout:
            typer.echo(result.stdout, nl=False)
        if not result.ok:
            typer.echo(result.stderr, err=True, nl=False)
            raise typer.Exit(result.returncode)
    except ToolNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("install")
def install_cmd(
    packages: list[str] = typer.Argument(..., help="One or more package names"),
) -> None:
    """Install one or more SDK packages."""
    result = sdkmanager.install(packages)
    if result.stdout:
        typer.echo(result.stdout, nl=False)
    if result.stderr:
        typer.echo(result.stderr, err=True, nl=False)
    if not result.ok:
        raise typer.Exit(result.returncode)


@app.command("update")
def update_cmd() -> None:
    """Update all installed SDK packages."""
    result = sdkmanager.update_all()
    if result.stdout:
        typer.echo(result.stdout, nl=False)
    if result.stderr:
        typer.echo(result.stderr, err=True, nl=False)
    if not result.ok:
        raise typer.Exit(result.returncode)


@app.command("remove")
def remove_cmd(
    packages: list[str] = typer.Argument(..., help="One or more package names"),
) -> None:
    """Remove one or more SDK packages."""
    result = sdkmanager.remove(packages)
    if result.stdout:
        typer.echo(result.stdout, nl=False)
    if result.stderr:
        typer.echo(result.stderr, err=True, nl=False)
    if not result.ok:
        raise typer.Exit(result.returncode)
