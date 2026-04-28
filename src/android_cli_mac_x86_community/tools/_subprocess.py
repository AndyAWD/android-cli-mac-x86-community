"""Shared subprocess helpers used by tool wrappers."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


class ToolNotFoundError(RuntimeError):
    pass


@dataclass
class ToolResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def _windows_executable_suffixes() -> list[str]:
    raw = os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD")
    return [s.lower() for s in raw.split(";") if s]


def _resolve_with_suffix(path: Path) -> Path | None:
    """On Windows, callers pass an extensionless absolute path (e.g. .../adb).
    Try each PATHEXT suffix to find the real executable.
    """
    if path.exists():
        return path
    if sys.platform != "win32":
        return None
    for suffix in _windows_executable_suffixes():
        candidate = path.with_name(path.name + suffix)
        if candidate.exists():
            return candidate
    return None


def resolve(executable: str | Path) -> Path:
    """Return an absolute Path to the executable, or raise ToolNotFoundError.

    Accepts either a bare name (looked up via PATH) or an absolute path.
    On Windows, an absolute path missing its executable suffix (.exe / .bat /
    ...) is probed against PATHEXT so callers can stay platform-neutral.
    """
    path = Path(executable)
    if path.is_absolute():
        resolved = _resolve_with_suffix(path)
        if resolved is None:
            raise ToolNotFoundError(f"{path} does not exist")
        return resolved
    found = shutil.which(str(executable))
    if not found:
        raise ToolNotFoundError(f"{executable} not found on PATH")
    return Path(found)


def run(executable: str | Path, args: list[str], *, check: bool = False,
        capture: bool = True, input_text: str | None = None) -> ToolResult:
    """Invoke an external tool. Pure subprocess wrapper, no shell."""
    exe = resolve(executable)
    proc = subprocess.run(
        [str(exe), *args],
        input=input_text,
        capture_output=capture,
        text=True,
    )
    result = ToolResult(
        returncode=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
    )
    if check and not result.ok:
        raise RuntimeError(
            f"{exe.name} {' '.join(args)} failed (exit {result.returncode}):\n"
            f"{result.stderr.strip()}"
        )
    return result
