"""`docs` — search and fetch Android documentation from a local KB index.

Mirrors the upstream `android docs` mechanism: download a public KB zip
from `dl.google.com/dac/dac_kb.zip`, build a SQLite FTS5 index over it,
and serve `search` / `fetch` queries entirely offline thereafter.
"""
from __future__ import annotations

import json
import sys
from typing import Optional

import typer

from ..utils import config, docs_index, docs_kb

app = typer.Typer(help="Android documentation commands", no_args_is_help=True)


def _ensure_ready(force_refresh: bool = False) -> None:
    zip_path = docs_kb.ensure_kb(force=force_refresh)
    docs_index.ensure_index(zip_path, config.docs_index_db_path())


@app.command("search")
def search_cmd(
    query: str = typer.Argument(..., help="Free-text search query"),
    limit: int = typer.Option(10, "--limit", "-n", min=1, max=100,
        help="Maximum number of results"),
    json_output: bool = typer.Option(False, "--json",
        help="Emit results as a JSON array"),
    refresh: bool = typer.Option(False, "--refresh",
        help="Force re-download of the KB zip (ignore local ETag)"),
) -> None:
    """Search Android documentation."""
    try:
        _ensure_ready(force_refresh=refresh)
        hits = docs_index.search(
            config.docs_index_db_path(), query, limit=limit
        )
    except (docs_kb.KBDownloadError, docs_index.DocsIndexError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1)

    if json_output:
        sys.stdout.write(
            json.dumps([h.to_dict() for h in hits], ensure_ascii=False) + "\n"
        )
        if not hits:
            raise typer.Exit(1)
        return

    if not hits:
        typer.echo(f"no results for: {query}", err=True)
        raise typer.Exit(1)

    for i, hit in enumerate(hits, 1):
        typer.echo(f"{i}. {hit.title}")
        typer.echo(f"   URL: {hit.kb_url}")
        if hit.short_description:
            typer.echo(f"   {hit.short_description}")


@app.command("fetch")
def fetch_cmd(
    url: str = typer.Argument(..., help="kb:// URL returned by `docs search`"),
) -> None:
    """Fetch the body of a KB entry as Markdown."""
    try:
        _ensure_ready()
        body = docs_index.fetch(config.docs_kb_zip_path(), url)
    except (docs_kb.KBDownloadError, docs_index.DocsIndexError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1)
    sys.stdout.write(body)
    if not body.endswith("\n"):
        sys.stdout.write("\n")
