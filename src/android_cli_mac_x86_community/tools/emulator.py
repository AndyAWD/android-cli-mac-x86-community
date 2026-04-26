"""Wrapper around the Android SDK `emulator` binary."""
from __future__ import annotations

import subprocess
from pathlib import Path

from ..utils.android_home import tool_path
from ._subprocess import ToolResult, run


def _emulator_path() -> Path:
    return tool_path("emulator/emulator")


def list_avd() -> ToolResult:
    return run(_emulator_path(), ["-list-avds"])


def start_detached(name: str, *, extra_args: list[str] | None = None) -> int:
    """Launch emulator in background. Returns the spawned PID.

    Caller is responsible for waiting on `adb wait-for-device` if it needs
    the emulator to be ready before issuing further commands.
    """
    args = [str(_emulator_path()), "-avd", name]
    if extra_args:
        args.extend(extra_args)
    proc = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return proc.pid
