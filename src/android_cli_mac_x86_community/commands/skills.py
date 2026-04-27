"""`skills` — manage agent skill packs from a public GitHub repo."""
from __future__ import annotations

import json
import sys
import tomllib
from typing import Optional

import typer

from ..utils import config, skills_repo

app = typer.Typer(help="Manage skills", no_args_is_help=True)


def _resolve_upstream(override: Optional[str]) -> str:
    if override:
        return override
    cfg_path = config.config_file()
    if cfg_path.exists():
        try:
            data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
            value = data.get("skills", {}).get("upstream")
            if isinstance(value, str) and value:
                return value
        except (tomllib.TOMLDecodeError, OSError):
            pass
    return skills_repo.DEFAULT_UPSTREAM


@app.command("list")
def list_cmd(
    upstream: Optional[str] = typer.Option(None, "--upstream",
        help="Override skills source repo (default: read from config.toml)"),
    json_output: bool = typer.Option(False, "--json",
        help="Emit results as a JSON array"),
    no_cache: bool = typer.Option(False, "--no-cache",
        help="Bypass the in-memory list cache"),
) -> None:
    """List skills available in the upstream repo."""
    src = _resolve_upstream(upstream)
    try:
        skills = skills_repo.list_skills(src, use_cache=not no_cache)
    except skills_repo.SkillsRepoError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1)

    if json_output:
        sys.stdout.write(
            json.dumps([s.name for s in skills], ensure_ascii=False) + "\n"
        )
        return

    if not skills:
        typer.echo(f"no skills found in {src}", err=True)
        return
    for s in skills:
        typer.echo(s.name)


@app.command("find")
def find_cmd(
    keyword: str = typer.Argument(..., help="Substring to match (case-insensitive)"),
    upstream: Optional[str] = typer.Option(None, "--upstream"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Filter the upstream skills list by keyword."""
    src = _resolve_upstream(upstream)
    try:
        skills = skills_repo.find_skills(keyword, src)
    except skills_repo.SkillsRepoError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1)

    if json_output:
        sys.stdout.write(
            json.dumps([s.name for s in skills], ensure_ascii=False) + "\n"
        )
        if not skills:
            raise typer.Exit(1)
        return

    if not skills:
        typer.echo(f"no skills matched: {keyword}", err=True)
        raise typer.Exit(1)
    for s in skills:
        typer.echo(s.name)


@app.command("add")
def add_cmd(
    name: str = typer.Argument(..., help="Skill name (top-level dir in upstream repo)"),
    upstream: Optional[str] = typer.Option(None, "--upstream"),
) -> None:
    """Download a skill into ~/.android-cli-mac-x86-community/skills/<name>/."""
    src = _resolve_upstream(upstream)
    config.skills_dir().mkdir(parents=True, exist_ok=True)
    try:
        path = skills_repo.download_skill(name, config.skills_dir(), src)
    except skills_repo.SkillsRepoError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1)
    typer.echo(f"installed {name} -> {path}")


@app.command("remove")
def remove_cmd(
    name: str = typer.Argument(..., help="Skill name to remove"),
) -> None:
    """Delete the local skill directory."""
    try:
        removed = skills_repo.remove_skill(name, config.skills_dir())
    except skills_repo.SkillsRepoError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1)
    if not removed:
        typer.echo(f"skill not installed: {name}", err=True)
        raise typer.Exit(1)
    typer.echo(f"removed {name}")
