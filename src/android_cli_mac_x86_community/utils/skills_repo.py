"""GitHub-backed skills catalog.

Lists and downloads skills from a public GitHub repository (default
`android/skills`). `list_skills` uses a process-local TTL cache to avoid
hammering the API on rapid `list` / `find` calls. `download_skill` fetches
the repo's default-branch tarball and extracts only the requested subtree.
"""
from __future__ import annotations

import io
import shutil
import tarfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

DEFAULT_UPSTREAM = "android/skills"
LIST_CACHE_TTL_SECONDS = 300.0
DEFAULT_TIMEOUT = 60.0

_GITHUB_API = "https://api.github.com"


class SkillsRepoError(RuntimeError):
    pass


@dataclass(frozen=True)
class Skill:
    name: str


# Module-level cache: {upstream: (expires_at, [Skill,...])}
_list_cache: dict[str, tuple[float, list[Skill]]] = {}


def _api_get(client: httpx.Client, path: str) -> httpx.Response:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    return client.get(f"{_GITHUB_API}{path}", headers=headers)


def _make_client() -> httpx.Client:
    return httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True)


def list_skills(
    upstream: str = DEFAULT_UPSTREAM,
    *,
    client: Optional[httpx.Client] = None,
    use_cache: bool = True,
) -> list[Skill]:
    """Return available skills (top-level directories) from the upstream repo."""
    now = time.monotonic()
    if use_cache:
        cached = _list_cache.get(upstream)
        if cached and cached[0] > now:
            return cached[1]

    owns = client is None
    if owns:
        client = _make_client()
    try:
        resp = _api_get(client, f"/repos/{upstream}/contents")
    finally:
        if owns:
            client.close()

    if resp.status_code != 200:
        raise SkillsRepoError(
            f"GitHub API returned {resp.status_code} for /repos/{upstream}/contents"
        )
    payload = resp.json()
    if not isinstance(payload, list):
        raise SkillsRepoError(
            f"unexpected GitHub response shape: {type(payload).__name__}"
        )
    skills = sorted(
        (Skill(name=item["name"]) for item in payload if item.get("type") == "dir"
         and not item["name"].startswith(".")),
        key=lambda s: s.name,
    )
    _list_cache[upstream] = (now + LIST_CACHE_TTL_SECONDS, skills)
    return skills


def find_skills(
    keyword: str,
    upstream: str = DEFAULT_UPSTREAM,
    *,
    client: Optional[httpx.Client] = None,
) -> list[Skill]:
    kw = keyword.lower()
    return [s for s in list_skills(upstream, client=client) if kw in s.name.lower()]


def _safe_extract_member(
    member: tarfile.TarInfo, target_root: Path, dest_root: Path
) -> Optional[tuple[tarfile.TarInfo, Path]]:
    """Resolve a tar member into a safe destination path, or None to skip.

    GitHub tarballs wrap everything in a top-level dir like
    `android-skills-<sha>/`; the caller passes that prefix joined with the
    skill name as `target_root` (e.g. `android-skills-<sha>/jetpack-compose`).
    Members outside that subtree are skipped. Members whose resolved path
    escapes `dest_root` (zip-slip) are rejected.
    """
    parts = member.name.split("/")
    target_parts = target_root.as_posix().split("/")
    if len(parts) <= len(target_parts) or parts[: len(target_parts)] != target_parts:
        return None
    rel_parts = parts[len(target_parts):]
    if not rel_parts or rel_parts == [""]:
        return None
    rel = Path(*rel_parts)
    out = (dest_root / rel).resolve()
    if dest_root.resolve() not in out.parents and out != dest_root.resolve():
        raise SkillsRepoError(f"unsafe tar member path: {member.name}")
    return member, out


def download_skill(
    name: str,
    dest: Path,
    upstream: str = DEFAULT_UPSTREAM,
    *,
    client: Optional[httpx.Client] = None,
) -> Path:
    """Fetch the upstream tarball and extract `<name>/` into `dest/<name>/`.

    Idempotent: if the destination exists, it's replaced atomically via a
    sibling temp directory so a partial extraction doesn't corrupt state.
    """
    if "/" in name or name in ("", ".", ".."):
        raise SkillsRepoError(f"invalid skill name: {name!r}")

    owns = client is None
    if owns:
        client = _make_client()
    try:
        resp = _api_get(client, f"/repos/{upstream}/tarball")
    finally:
        if owns:
            client.close()
    if resp.status_code != 200:
        raise SkillsRepoError(
            f"GitHub API returned {resp.status_code} for /repos/{upstream}/tarball"
        )

    dest.mkdir(parents=True, exist_ok=True)
    final_path = dest / name
    staging = dest / f".{name}.partial"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    extracted_any = False
    with tarfile.open(fileobj=io.BytesIO(resp.content), mode="r:gz") as tf:
        # Discover tarball's wrapping directory (e.g. android-skills-<sha>/).
        first = next((m for m in tf.getmembers() if "/" in m.name), None)
        if first is None:
            raise SkillsRepoError("empty or unexpected tarball layout")
        wrapper = first.name.split("/", 1)[0]
        target_root = Path(wrapper) / name

        for member in tf.getmembers():
            resolved = _safe_extract_member(member, target_root, staging)
            if resolved is None:
                continue
            tar_member, out_path = resolved
            if tar_member.isdir():
                out_path.mkdir(parents=True, exist_ok=True)
                continue
            if not (tar_member.isfile() or tar_member.isreg()):
                continue
            out_path.parent.mkdir(parents=True, exist_ok=True)
            src = tf.extractfile(tar_member)
            if src is None:
                continue
            with out_path.open("wb") as f:
                shutil.copyfileobj(src, f)
            extracted_any = True

    if not extracted_any:
        shutil.rmtree(staging, ignore_errors=True)
        raise SkillsRepoError(
            f"skill {name!r} not found in upstream {upstream!r}"
        )

    if final_path.exists():
        shutil.rmtree(final_path)
    staging.replace(final_path)
    return final_path


def remove_skill(name: str, dest: Path) -> bool:
    """Remove `dest/<name>/`. Returns True if removed, False if absent."""
    if "/" in name or name in ("", ".", ".."):
        raise SkillsRepoError(f"invalid skill name: {name!r}")
    target = dest / name
    if not target.exists():
        return False
    shutil.rmtree(target)
    return True


def clear_list_cache() -> None:
    _list_cache.clear()
