"""`update` — self-update the CLI from GitHub."""
from __future__ import annotations

from typing import Optional

import typer

from .. import __version__
from ..utils import self_update


def update_cmd(
    url: Optional[str] = typer.Option(None, "--url",
        help="Install from this pip target instead of the default GitHub repo"),
    repo: str = typer.Option(self_update.DEFAULT_REPO, "--repo",
        help="GitHub <owner>/<name> to query for releases"),
    check: bool = typer.Option(False, "--check",
        help="Only check for the latest release; do not install"),
) -> None:
    """Upgrade this CLI to the latest GitHub release (via pip)."""
    if url:
        if check:
            typer.echo(
                "error: --check and --url are mutually exclusive", err=True
            )
            raise typer.Exit(2)
        typer.echo(f"installing from: {url}")
        rc = self_update.run_pip_install(url)
        raise typer.Exit(rc)

    try:
        release = self_update.latest_release(repo)
    except self_update.SelfUpdateError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1)

    typer.echo(f"current: {__version__}")
    if release is None:
        typer.echo(f"no published releases at {repo}")
        # Without releases, fall back to installing the default branch on
        # explicit non-check runs; in --check mode there's nothing to do.
        if check:
            return
        target = self_update.default_install_target(repo)
        typer.echo(f"installing default branch: {target}")
        rc = self_update.run_pip_install(target)
        raise typer.Exit(rc)

    typer.echo(f"latest:  {release.tag_name}  ({release.html_url})")

    if not self_update.is_newer(release.tag_name, __version__):
        typer.echo("already up to date")
        return

    if check:
        return

    target = self_update.default_install_target(repo, release.tag_name)
    typer.echo(f"installing: {target}")
    rc = self_update.run_pip_install(target)
    raise typer.Exit(rc)
