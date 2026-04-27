"""Discover the Android SDK location on the host machine."""
from __future__ import annotations

import os
from pathlib import Path


class SdkNotFoundError(RuntimeError):
    pass


def _platform_default_sdk_paths() -> list[Path]:
    """Per-OS default install locations Android Studio uses out of the box."""
    candidates: list[Path] = []
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        candidates.append(Path(local_appdata) / "Android" / "Sdk")
    candidates.extend([
        Path.home() / "Library" / "Android" / "sdk",  # macOS
        Path.home() / "AppData" / "Local" / "Android" / "Sdk",  # Windows fallback
        Path.home() / "Android" / "Sdk",  # Linux
    ])
    return candidates


def find_sdk_root() -> Path:
    """Return the Android SDK root, or raise SdkNotFoundError.

    Resolution order matches the convention used by Android tooling:
    1. $ANDROID_HOME
    2. $ANDROID_SDK_ROOT
    3. %LOCALAPPDATA%\\Android\\Sdk (Windows default, Android Studio)
    4. ~/Library/Android/sdk (macOS default)
    5. ~/AppData/Local/Android/Sdk (Windows fallback when LOCALAPPDATA unset)
    6. ~/Android/Sdk (Linux default)
    """
    for env_var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        value = os.environ.get(env_var)
        if value:
            path = Path(value).expanduser()
            if path.is_dir():
                return path

    seen: set[Path] = set()
    for default in _platform_default_sdk_paths():
        if default in seen:
            continue
        seen.add(default)
        if default.is_dir():
            return default

    raise SdkNotFoundError(
        "Android SDK not found. Set ANDROID_HOME or install command-line tools to "
        "~/Library/Android/sdk per https://developer.android.com/studio#command-line-tools-only"
    )


def tool_path(relative: str) -> Path:
    """Return absolute path to a tool within the SDK, e.g. 'platform-tools/adb'."""
    return find_sdk_root() / relative
