"""`screen` — view the device."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer

from ..tools import adb
from ..utils.layout_xml import find_nodes, parse_bounds
from ..utils.uiautomator import capture_layout_xml

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


@app.command("resolve")
def resolve_cmd(
    text: Optional[str] = typer.Option(None, "--text",
        help="Match exact text content"),
    resource_id: Optional[str] = typer.Option(None, "--id",
        help="Match exact resource-id"),
    content_desc: Optional[str] = typer.Option(None, "--desc",
        help="Match exact content-desc"),
    class_name: Optional[str] = typer.Option(None, "--class",
        help="Match exact class"),
    device: Optional[str] = typer.Option(None, "--device",
        help="Target device serial number"),
    pretty: bool = typer.Option(False, "--pretty", "-p",
        help="Pretty-print the JSON output"),
) -> None:
    """Locate UI elements in the foreground app's view hierarchy.

    Returns a JSON list of matching nodes; bounds are parsed into
    {x1,y1,x2,y2,cx,cy}. Exits 1 when no node matches, 2 when no selector
    is given.
    """
    if all(s is None for s in (text, resource_id, content_desc, class_name)):
        typer.echo(
            "error: provide at least one of --text, --id, --desc, --class",
            err=True,
        )
        raise typer.Exit(2)

    xml_text = capture_layout_xml(device)
    nodes = find_nodes(
        xml_text,
        text=text,
        resource_id=resource_id,
        content_desc=content_desc,
        class_name=class_name,
    )

    out: list[dict] = []
    for node in nodes:
        attrs = dict(node["attrs"])
        raw_bounds = attrs.pop("bounds", "")
        parsed = parse_bounds(raw_bounds)
        attrs["bounds"] = parsed if parsed is not None else raw_bounds
        out.append(attrs)

    indent = 2 if pretty else None
    sys.stdout.write(json.dumps(out, indent=indent, ensure_ascii=False) + "\n")

    if not nodes:
        raise typer.Exit(1)
