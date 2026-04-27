from __future__ import annotations

import sys

import httpx
import pytest
from typer.testing import CliRunner

from android_cli_mac_x86_community import __version__
from android_cli_mac_x86_community.cli import app
from android_cli_mac_x86_community.utils import self_update


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ---------- pure helpers ---------------------------------------------------

def test_is_newer_strips_v_prefix():
    assert self_update.is_newer("v0.2.0", "0.1.0") is True
    assert self_update.is_newer("0.1.0", "v0.1.0") is False


def test_is_newer_equal_versions():
    assert self_update.is_newer("0.1.0", "0.1.0") is False


def test_pip_install_command_uses_current_python():
    cmd = self_update.pip_install_command("git+https://x/y.git@v1.0")
    assert cmd[0] == sys.executable
    assert cmd[1:4] == ["-m", "pip", "install"]
    assert "--upgrade" in cmd
    assert cmd[-1] == "git+https://x/y.git@v1.0"


def test_default_install_target_with_tag():
    assert (
        self_update.default_install_target("foo/bar", "v1.2.3")
        == "git+https://github.com/foo/bar.git@v1.2.3"
    )


def test_default_install_target_without_tag():
    assert (
        self_update.default_install_target("foo/bar")
        == "git+https://github.com/foo/bar.git"
    )


# ---------- latest_release with mocked GitHub ------------------------------

def test_latest_release_returns_release():
    payload = {
        "tag_name": "v0.2.0",
        "html_url": "https://github.com/foo/bar/releases/tag/v0.2.0",
        "tarball_url": "https://api.github.com/repos/foo/bar/tarball/v0.2.0",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/repos/foo/bar/releases/latest")
        return httpx.Response(200, json=payload)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        rel = self_update.latest_release("foo/bar", client=client)
    assert rel is not None
    assert rel.tag_name == "v0.2.0"
    assert "v0.2.0" in rel.html_url


def test_latest_release_returns_none_on_404():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        rel = self_update.latest_release("foo/bar", client=client)
    assert rel is None


def test_latest_release_raises_on_unexpected_status():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(self_update.SelfUpdateError):
            self_update.latest_release("foo/bar", client=client)


# ---------- CLI tests ------------------------------------------------------

def test_update_check_already_up_to_date(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    rel = self_update.Release(
        tag_name=f"v{__version__}",
        html_url="https://example/release",
        tarball_url="",
    )
    monkeypatch.setattr(self_update, "latest_release", lambda repo: rel)
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.update.self_update.latest_release",
        lambda repo: rel,
    )
    pip_calls = []
    monkeypatch.setattr(
        self_update, "run_pip_install",
        lambda target: pip_calls.append(target) or 0,
    )
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.update.self_update.run_pip_install",
        lambda target: pip_calls.append(target) or 0,
    )

    result = runner.invoke(app, ["update", "--check"])
    assert result.exit_code == 0, result.output
    assert "already up to date" in result.output
    assert pip_calls == []


def test_update_check_newer_available(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    rel = self_update.Release(
        tag_name="v999.0.0",
        html_url="https://example/release",
        tarball_url="",
    )
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.update.self_update.latest_release",
        lambda repo: rel,
    )
    pip_calls: list[str] = []
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.update.self_update.run_pip_install",
        lambda target: pip_calls.append(target) or 0,
    )

    result = runner.invoke(app, ["update", "--check"])
    assert result.exit_code == 0, result.output
    assert "v999.0.0" in result.output
    # --check must not install.
    assert pip_calls == []


def test_update_installs_when_newer(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    rel = self_update.Release(
        tag_name="v999.0.0",
        html_url="https://example/release",
        tarball_url="",
    )
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.update.self_update.latest_release",
        lambda repo: rel,
    )
    pip_calls: list[str] = []
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.update.self_update.run_pip_install",
        lambda target: pip_calls.append(target) or 0,
    )

    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0, result.output
    assert pip_calls == [
        "git+https://github.com/AndyAWD/android-cli-mac-x86-community.git@v999.0.0"
    ]


def test_update_no_releases_falls_back_to_default_branch(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.update.self_update.latest_release",
        lambda repo: None,
    )
    pip_calls: list[str] = []
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.update.self_update.run_pip_install",
        lambda target: pip_calls.append(target) or 0,
    )

    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0, result.output
    assert pip_calls == [
        "git+https://github.com/AndyAWD/android-cli-mac-x86-community.git"
    ]


def test_update_check_no_releases(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.update.self_update.latest_release",
        lambda repo: None,
    )
    pip_calls: list[str] = []
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.update.self_update.run_pip_install",
        lambda target: pip_calls.append(target) or 0,
    )

    result = runner.invoke(app, ["update", "--check"])
    assert result.exit_code == 0, result.output
    assert "no published releases" in result.output
    assert pip_calls == []


def test_update_with_url(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    pip_calls: list[str] = []
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.update.self_update.run_pip_install",
        lambda target: pip_calls.append(target) or 0,
    )

    result = runner.invoke(app, ["update", "--url", "/local/path/to/wheel.whl"])
    assert result.exit_code == 0, result.output
    assert pip_calls == ["/local/path/to/wheel.whl"]


def test_update_url_and_check_are_mutually_exclusive(runner: CliRunner):
    result = runner.invoke(
        app, ["update", "--url", "x", "--check"]
    )
    assert result.exit_code == 2
    out = result.output + (result.stderr or "")
    assert "mutually exclusive" in out


def test_update_propagates_pip_failure(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    rel = self_update.Release(tag_name="v999.0.0", html_url="", tarball_url="")
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.update.self_update.latest_release",
        lambda repo: rel,
    )
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.update.self_update.run_pip_install",
        lambda target: 7,
    )

    result = runner.invoke(app, ["update"])
    assert result.exit_code == 7


def test_update_api_error_exits_1(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    def boom(repo):
        raise self_update.SelfUpdateError("api down")

    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.update.self_update.latest_release",
        boom,
    )
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 1
    out = result.output + (result.stderr or "")
    assert "api down" in out
