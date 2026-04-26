import typer

from . import DISCLAIMER, __version__
from .commands import emulator, info, run, screen, sdk

app = typer.Typer(
    name="android-cli-mac-x86-community",
    help="Unofficial community port of Android CLI for Intel macOS (x86_64).",
    no_args_is_help=True,
    epilog=DISCLAIMER,
)

app.add_typer(sdk.app, name="sdk", help="Download and list SDK packages")
app.add_typer(emulator.app, name="emulator", help="Emulator commands")
app.add_typer(screen.app, name="screen", help="Commands to view the device")
app.command(name="info", help="Print environment information")(info.info_cmd)
app.command(name="run", help="Deploy an Android application")(run.run_cmd)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"android-cli-mac-x86-community {__version__}")
        typer.echo("")
        typer.echo(DISCLAIMER)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-V", callback=_version_callback, is_eager=True,
        help="Print version and exit."
    ),
) -> None:
    pass
