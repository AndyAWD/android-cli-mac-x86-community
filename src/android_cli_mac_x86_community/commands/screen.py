"""`screen` — view the device."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer

from ..tools import adb

app = typer.Typer(help="Commands to view the device", no_args_is_help=True)


@app.command("capture")
def capture_cmd(
    output: Optional[Path] = typer.Option(None, "--output", "-o",
        help="Write PNG to file. If omitted, raw bytes go to stdout."),
    device: Optional[str] = typer.Option(None, "--device",
        help="Target device serial number"),
) -> None:
    """Capture the device screen as PNG."""
    png = adb.screencap_png(serial=device)
    if output is None:
        sys.stdout.buffer.write(png)
        return
    output.write_bytes(png)
    typer.echo(f"wrote {len(png)} bytes to {output}")
