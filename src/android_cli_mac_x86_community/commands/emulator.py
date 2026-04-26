"""`emulator` — manage AVDs."""
from __future__ import annotations

import typer

from ..tools import avdmanager
from ..tools import emulator as emu_tool

app = typer.Typer(help="Emulator commands", no_args_is_help=True)


@app.command("list")
def list_cmd() -> None:
    """List available virtual devices."""
    result = emu_tool.list_avd()
    if result.stdout:
        typer.echo(result.stdout, nl=False)
    if not result.ok:
        typer.echo(result.stderr, err=True, nl=False)
        raise typer.Exit(result.returncode)


@app.command("create")
def create_cmd(
    name: str = typer.Option(..., "--name", help="AVD name"),
    image: str = typer.Option(..., "--image",
        help="System image package, e.g. 'system-images;android-34;google_apis;x86_64'"),
    device: str | None = typer.Option(None, "--device", help="Device profile"),
    force: bool = typer.Option(False, "--force", help="Overwrite if AVD exists"),
) -> None:
    """Create a virtual device."""
    result = avdmanager.create(name, image, device=device, force=force)
    if result.stdout:
        typer.echo(result.stdout, nl=False)
    if result.stderr:
        typer.echo(result.stderr, err=True, nl=False)
    if not result.ok:
        raise typer.Exit(result.returncode)
    typer.echo(f"Created AVD: {name}")


@app.command("start")
def start_cmd(
    name: str = typer.Option(..., "--name", help="AVD name to start"),
) -> None:
    """Launch the specified virtual device (detached)."""
    pid = emu_tool.start_detached(name)
    typer.echo(f"Emulator '{name}' launched (pid {pid}).")
    typer.echo("Use `adb wait-for-device` if you need to block until it's ready.")
