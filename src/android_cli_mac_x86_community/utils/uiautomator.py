"""Pull a uiautomator window dump from the connected device."""
from __future__ import annotations

import tempfile
from pathlib import Path

import typer

from ..tools import adb


def capture_layout_xml(serial: str | None = None) -> str:
    """Run uiautomator dump on the device and return the XML text.

    Raises typer.Exit when the dump or pull step fails so callers can let it
    propagate up to the CLI exit code.
    """
    dump = adb.uiautomator_dump(serial=serial)
    if not dump.ok:
        raise typer.Exit(dump.returncode or 1)
    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp) / "window_dump.xml"
        pull = adb.pull("/sdcard/window_dump.xml", local, serial=serial)
        if not pull.ok:
            typer.echo(pull.stderr, err=True, nl=False)
            raise typer.Exit(pull.returncode or 1)
        return local.read_text(encoding="utf-8")
