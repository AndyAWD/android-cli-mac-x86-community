from __future__ import annotations

from pathlib import Path

import pytest

from android_cli_mac_x86_community.utils.android_home import (
    SdkNotFoundError,
    find_sdk_root,
)


def test_finds_via_android_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANDROID_HOME", str(tmp_path))
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)
    assert find_sdk_root() == tmp_path


def test_prefers_android_home_over_sdk_root(tmp_path: Path,
                                            monkeypatch: pytest.MonkeyPatch):
    home = tmp_path / "home"
    root = tmp_path / "root"
    home.mkdir()
    root.mkdir()
    monkeypatch.setenv("ANDROID_HOME", str(home))
    monkeypatch.setenv("ANDROID_SDK_ROOT", str(root))
    assert find_sdk_root() == home


def test_raises_when_nothing_found(tmp_path: Path,
                                   monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    with pytest.raises(SdkNotFoundError):
        find_sdk_root()


def test_finds_via_localappdata(tmp_path: Path,
                                monkeypatch: pytest.MonkeyPatch):
    """Windows: Android Studio installs under %LOCALAPPDATA%\\Android\\Sdk."""
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)
    sdk = tmp_path / "Android" / "Sdk"
    sdk.mkdir(parents=True)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    # Make sure other defaults don't accidentally win.
    monkeypatch.setenv("HOME", str(tmp_path / "elsewhere"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "elsewhere"))
    assert find_sdk_root() == sdk
