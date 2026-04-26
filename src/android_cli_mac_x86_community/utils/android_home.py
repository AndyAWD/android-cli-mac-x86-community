"""Discover the Android SDK location on the host machine."""
from __future__ import annotations

import os
from pathlib import Path


class SdkNotFoundError(RuntimeError):
    pass


def find_sdk_root() -> Path:
    """Return the Android SDK root, or raise SdkNotFoundError.

    Resolution order matches the convention used by Android tooling:
    1. $ANDROID_HOME
    2. $ANDROID_SDK_ROOT
    3. ~/Library/Android/sdk (macOS default)
    4. ~/Android/Sdk (Linux default, kept for dev on non-Mac hosts)
    """
    for env_var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        value = os.environ.get(env_var)
        if value:
            path = Path(value).expanduser()
            if path.is_dir():
                return path

    for default in (
        Path.home() / "Library" / "Android" / "sdk",
        Path.home() / "Android" / "Sdk",
    ):
        if default.is_dir():
            return default

    raise SdkNotFoundError(
        "Android SDK not found. Set ANDROID_HOME or install command-line tools to "
        "~/Library/Android/sdk per https://developer.android.com/studio#command-line-tools-only"
    )


def tool_path(relative: str) -> Path:
    """Return absolute path to a tool within the SDK, e.g. 'platform-tools/adb'."""
    return find_sdk_root() / relative
