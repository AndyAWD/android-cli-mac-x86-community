"""Wrapper around the Android SDK `sdkmanager` binary."""
from __future__ import annotations

from pathlib import Path

from ..utils.android_home import tool_path
from ._subprocess import ToolResult, run


def _sdkmanager_path() -> Path:
    return tool_path("cmdline-tools/latest/bin/sdkmanager")


def list_packages() -> ToolResult:
    return run(_sdkmanager_path(), ["--list"])


def install(packages: list[str]) -> ToolResult:
    if not packages:
        raise ValueError("install requires at least one package name")
    return run(_sdkmanager_path(), [*packages], input_text="y\n")


def update_all() -> ToolResult:
    return run(_sdkmanager_path(), ["--update"], input_text="y\n")


def remove(packages: list[str]) -> ToolResult:
    if not packages:
        raise ValueError("remove requires at least one package name")
    return run(_sdkmanager_path(), ["--uninstall", *packages])
