"""Wrapper around the Android SDK `avdmanager` binary."""
from __future__ import annotations

from pathlib import Path

from ..utils.android_home import tool_path
from ._subprocess import ToolResult, run


def _avdmanager_path() -> Path:
    return tool_path("cmdline-tools/latest/bin/avdmanager")


def list_avd() -> ToolResult:
    return run(_avdmanager_path(), ["list", "avd"])


def create(name: str, image: str, *, device: str | None = None,
           force: bool = False) -> ToolResult:
    args = ["create", "avd", "--name", name, "--package", image]
    if device:
        args += ["--device", device]
    if force:
        args.append("--force")
    return run(_avdmanager_path(), args, input_text="no\n")


def delete(name: str) -> ToolResult:
    return run(_avdmanager_path(), ["delete", "avd", "--name", name])
