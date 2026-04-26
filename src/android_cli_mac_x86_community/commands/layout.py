"""`layout` — dump and (optionally) diff the UI hierarchy."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Optional

import typer

from ..tools import adb
from ..utils.config import config_root, layout_snapshot_path
from ..utils.layout_xml import diff_trees, xml_to_tree


def _capture_xml(serial: str | None) -> str:
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


def layout_cmd(
    diff: bool = typer.Option(False, "--diff", "-d",
        help="Return changes since the last invocation"),
    device: Optional[str] = typer.Option(None, "--device",
        help="Target device serial number"),
    output: Optional[Path] = typer.Option(None, "--output", "-o",
        help="Write the result to file instead of stdout"),
    pretty: bool = typer.Option(False, "--pretty", "-p",
        help="Pretty-print the JSON"),
) -> None:
    """Return the layout tree of the foreground application."""
    xml_text = _capture_xml(device)
    indent = 2 if pretty else None

    if diff:
        snapshot = layout_snapshot_path()
        prev = snapshot.read_text(encoding="utf-8") if snapshot.exists() else ""
        result: object = diff_trees(prev, xml_text)
    else:
        result = xml_to_tree(xml_text)

    config_root().mkdir(parents=True, exist_ok=True)
    layout_snapshot_path().write_text(xml_text, encoding="utf-8")

    payload = json.dumps(result, indent=indent, ensure_ascii=False)
    if output:
        output.write_text(payload + "\n", encoding="utf-8")
        typer.echo(f"wrote {output}", err=True)
    else:
        sys.stdout.write(payload + "\n")
