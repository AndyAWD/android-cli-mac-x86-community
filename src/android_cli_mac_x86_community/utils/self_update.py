"""Self-update helpers: check GitHub Releases and shell out to pip.

The actual install is delegated to the pip executable in the current
Python environment (`sys.executable -m pip install --upgrade ...`),
which handles network, dependency resolution, and replacement of the
installed entry-point script. This module does not touch site-packages
directly — that would be fragile across macOS / Windows / venv setups.
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

import httpx

DEFAULT_REPO = "AndyAWD/android-cli-mac-x86-community"
_GITHUB_API = "https://api.github.com"
DEFAULT_TIMEOUT = 30.0


class SelfUpdateError(RuntimeError):
    pass


@dataclass(frozen=True)
class Release:
    tag_name: str
    html_url: str
    tarball_url: str


def _normalize_version(s: str) -> str:
    """Drop a leading 'v' and surrounding whitespace for tag-vs-version compare."""
    s = s.strip()
    if s.startswith("v"):
        s = s[1:]
    return s


def latest_release(
    repo: str = DEFAULT_REPO,
    *,
    client: Optional[httpx.Client] = None,
) -> Optional[Release]:
    """Return the latest published release, or None if the repo has no releases."""
    owns = client is None
    if owns:
        client = httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True)
    try:
        resp = client.get(
            f"{_GITHUB_API}/repos/{repo}/releases/latest",
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
    finally:
        if owns:
            client.close()

    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise SelfUpdateError(
            f"GitHub API returned {resp.status_code} for /repos/{repo}/releases/latest"
        )
    data = resp.json()
    tag = data.get("tag_name", "")
    if not tag:
        return None
    return Release(
        tag_name=tag,
        html_url=data.get("html_url", ""),
        tarball_url=data.get("tarball_url", ""),
    )


def is_newer(latest_tag: str, current: str) -> bool:
    """True iff `latest_tag` differs from `current` after stripping a `v` prefix.

    We don't try semver-aware ordering — pip's resolver is the source of
    truth on whether an upgrade actually happens. Equality is enough to
    short-circuit the "already up to date" message.
    """
    return _normalize_version(latest_tag) != _normalize_version(current)


def pip_install_command(target: str) -> list[str]:
    """Return the argv for upgrading the package to `target` (URL / spec)."""
    return [sys.executable, "-m", "pip", "install", "--upgrade", target]


def run_pip_install(target: str) -> int:
    """Run pip install --upgrade <target>. Returns the pip exit code."""
    proc = subprocess.run(pip_install_command(target))
    return proc.returncode


def default_install_target(repo: str = DEFAULT_REPO, tag: Optional[str] = None) -> str:
    """Build the pip-installable git URL for the repo (optionally pinned to a tag)."""
    base = f"git+https://github.com/{repo}.git"
    return f"{base}@{tag}" if tag else base
