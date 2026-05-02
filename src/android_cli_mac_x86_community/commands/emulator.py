"""`emulator` — manage AVDs."""
from __future__ import annotations

import time
import typer

from ..tools import adb, avdmanager
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
    wait_boot: bool = typer.Option(False, "--wait-boot", help="Wait for the emulator to fully boot"),
    unlock: bool = typer.Option(False, "--unlock", help="Unlock the screen after booting"),
) -> None:
    """Launch the specified virtual device (detached)."""
    pid = emu_tool.start_detached(name)
    typer.echo(f"Emulator '{name}' launched (pid {pid}).")

    if wait_boot or unlock:
        typer.echo("Waiting for emulator to become discoverable...")
        serial = None
        for _ in range(60):  # Wait up to 60 seconds to find the serial
            serial = adb.find_emulator_serial_by_avd(name)
            if serial:
                break
            time.sleep(1)

        if not serial:
            typer.echo("Warning: Could not discover emulator serial within 60 seconds.", err=True)
            return

        typer.echo(f"Emulator attached as {serial}. Waiting for device...")
        adb.wait_for_device(serial)

        if wait_boot:
            typer.echo("Waiting for boot animation to finish...")
            for _ in range(300):  # Wait up to 5 minutes for boot
                res = adb.shell("getprop sys.boot_completed", serial=serial)
                if res.stdout and res.stdout.strip() == "1":
                    break
                time.sleep(2)
            else:
                typer.echo("Warning: Timeout waiting for sys.boot_completed.", err=True)

            # Check for SystemUI ANR
            typer.echo("Checking for SystemUI ANR...")
            res = adb.shell("dumpsys window windows", serial=serial)
            if res.stdout and "Application Not Responding" in res.stdout and "com.android.systemui" in res.stdout:
                typer.echo("Detected SystemUI ANR, restarting SystemUI...")
                adb.shell("am crash com.android.systemui", serial=serial)

        if unlock:
            typer.echo("Unlocking screen...")
            # Key 82 = MENU (often dismisses lock screen on older Android), 4 = BACK
            adb.shell("input keyevent 82", serial=serial)
            time.sleep(0.5)
            adb.shell("input keyevent 4", serial=serial)

        typer.echo("Emulator is ready.")
    else:
        typer.echo("Use `adb wait-for-device` if you need to block until it's ready.")


@app.command("stop")
def stop_cmd(
    name: str = typer.Option(..., "--name", help="AVD name to stop"),
) -> None:
    """Stop a running virtual device by AVD name."""
    serial = adb.find_emulator_serial_by_avd(name)
    if serial is None:
        typer.echo(f"No running emulator found with AVD name '{name}'.", err=True)
        raise typer.Exit(1)
    result = adb.emu_kill(serial)
    if result.stdout:
        typer.echo(result.stdout, nl=False)
    if not result.ok:
        typer.echo(result.stderr, err=True, nl=False)
        raise typer.Exit(result.returncode)
    typer.echo(f"Stopped emulator '{name}' ({serial}).")


@app.command("remove")
def remove_cmd(
    name: str = typer.Option(..., "--name", help="AVD name to delete"),
) -> None:
    """Delete a virtual device."""
    result = avdmanager.delete(name)
    if result.stdout:
        typer.echo(result.stdout, nl=False)
    if result.stderr:
        typer.echo(result.stderr, err=True, nl=False)
    if not result.ok:
        raise typer.Exit(result.returncode)
    typer.echo(f"Deleted AVD: {name}")
