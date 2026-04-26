"""`sdk` — manage Android SDK packages via sdkmanager."""
from __future__ import annotations

import typer

from ..tools import sdkmanager

app = typer.Typer(help="Download and list SDK packages", no_args_is_help=True)


@app.command("list")
def list_cmd() -> None:
    """List installed and available SDK packages."""
    result = sdkmanager.list_packages()
    if result.stdout:
        typer.echo(result.stdout, nl=False)
    if not result.ok:
        typer.echo(result.stderr, err=True, nl=False)
        raise typer.Exit(result.returncode)


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
