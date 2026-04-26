from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fake_sdk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a fake SDK tree on disk and point ANDROID_HOME at it.

    Layout matches what the wrappers expect: platform-tools/adb,
    cmdline-tools/latest/bin/{sdkmanager,avdmanager}, emulator/emulator.
    Each "binary" is just an empty file so resolve() succeeds.
    """
    for rel in (
        "platform-tools/adb",
        "cmdline-tools/latest/bin/sdkmanager",
        "cmdline-tools/latest/bin/avdmanager",
        "emulator/emulator",
    ):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
    monkeypatch.setenv("ANDROID_HOME", str(tmp_path))
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)
    return tmp_path
