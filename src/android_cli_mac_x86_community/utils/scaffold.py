"""Render a project from a template directory of .tmpl files.

Variable syntax in both file content and path segments is `{{name}}`. Files
are sourced from a template root, with `.tmpl` stripped from the destination
name. The literal segment `_gitignore` becomes `.gitignore` so the template
directory itself is not affected by gitignore rules.
"""
from __future__ import annotations

from pathlib import Path


class TargetNotEmptyError(RuntimeError):
    """Raised when scaffold() is asked to write into a non-empty directory."""


def render(text: str, vars: dict[str, str]) -> str:
    """Substitute every `{{key}}` occurrence with the matching value."""
    for key, value in vars.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def _rewrite_gitignore_marker(rel: str) -> str:
    if rel == "_gitignore" or rel.endswith("/_gitignore"):
        return rel[: -len("_gitignore")] + ".gitignore"
    return rel


def scaffold(
    template_root: Path,
    target_root: Path,
    vars: dict[str, str],
) -> list[Path]:
    """Materialise template_root into target_root with vars applied.

    Returns the list of created file paths (relative to target_root).
    Raises TargetNotEmptyError if target_root exists and is non-empty.
    """
    if target_root.exists() and any(target_root.iterdir()):
        raise TargetNotEmptyError(f"{target_root} is not empty")
    target_root.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    for src in sorted(template_root.rglob("*.tmpl")):
        rel = src.relative_to(template_root).as_posix()[: -len(".tmpl")]
        rel = render(rel, vars)
        rel = _rewrite_gitignore_marker(rel)
        dest = target_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render(src.read_text(encoding="utf-8"), vars),
                        encoding="utf-8")
        created.append(Path(rel))
    return created
