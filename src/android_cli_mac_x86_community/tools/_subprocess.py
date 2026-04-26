"""Shared subprocess helpers used by tool wrappers."""
from __future__ import annotations

import shutil
import subprocess
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


def resolve(executable: str | Path) -> Path:
    """Return an absolute Path to the executable, or raise ToolNotFoundError.

    Accepts either a bare name (looked up via PATH) or an absolute path.
    """
    path = Path(executable)
    if path.is_absolute():
        if not path.exists():
            raise ToolNotFoundError(f"{path} does not exist")
        return path
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
