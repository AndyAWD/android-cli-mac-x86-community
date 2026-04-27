from __future__ import annotations

import io
import json
import tarfile
import time
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from android_cli_mac_x86_community.cli import app
from android_cli_mac_x86_community.utils import config, skills_repo


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(config, "config_root", lambda: tmp_path / "cfg")
    return tmp_path


@pytest.fixture(autouse=True)
def clear_skills_cache():
    skills_repo.clear_list_cache()
    yield
    skills_repo.clear_list_cache()


# ---------- helpers ---------------------------------------------------------

def _contents_payload() -> list[dict]:
    return [
        {"name": ".github", "type": "dir"},
        {"name": "LICENSE.txt", "type": "file"},
        {"name": "README.md", "type": "file"},
        {"name": "build", "type": "dir"},
        {"name": "jetpack-compose", "type": "dir"},
        {"name": "navigation", "type": "dir"},
        {"name": "play", "type": "dir"},
    ]


def _build_repo_tarball(skills: dict[str, dict[str, str]],
                        wrapper: str = "android-skills-abc1234") -> bytes:
    """Build a tarball mimicking GitHub's `/tarball` shape.

    `skills` maps skill_name -> {relative_path: file_content}.
    """
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        # Top-level wrapper dir.
        info = tarfile.TarInfo(wrapper)
        info.type = tarfile.DIRTYPE
        info.mode = 0o755
        tf.addfile(info)
        for skill_name, files in skills.items():
            for relpath, content in files.items():
                full = f"{wrapper}/{skill_name}/{relpath}"
                data = content.encode("utf-8")
                ti = tarfile.TarInfo(full)
                ti.size = len(data)
                ti.mode = 0o644
                tf.addfile(ti, io.BytesIO(data))
    return buf.getvalue()


def _mock_transport(handlers: dict[str, httpx.Response]) -> httpx.MockTransport:
    """Map URL paths to canned responses."""
    def handle(request: httpx.Request) -> httpx.Response:
        for path_suffix, resp in handlers.items():
            if request.url.path.endswith(path_suffix):
                return resp
        return httpx.Response(404, json={"message": f"unmocked: {request.url}"})
    return httpx.MockTransport(handle)


# ---------- list / find unit tests -----------------------------------------

def test_list_skills_returns_only_dirs():
    transport = _mock_transport({
        "/repos/android/skills/contents": httpx.Response(200, json=_contents_payload()),
    })
    with httpx.Client(transport=transport) as client:
        skills = skills_repo.list_skills(client=client, use_cache=False)
    names = [s.name for s in skills]
    assert names == ["build", "jetpack-compose", "navigation", "play"]
    assert ".github" not in names
    assert "README.md" not in names


def test_list_skills_uses_cache():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=_contents_payload())

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        skills_repo.list_skills(client=client)
        skills_repo.list_skills(client=client)
        skills_repo.list_skills(client=client)
    assert calls["n"] == 1


def test_list_skills_no_cache_bypasses():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=_contents_payload())

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        skills_repo.list_skills(client=client, use_cache=True)
        skills_repo.list_skills(client=client, use_cache=False)
    assert calls["n"] == 2


def test_list_skills_raises_on_api_error():
    transport = _mock_transport({
        "/repos/android/skills/contents": httpx.Response(404, json={"message": "Not Found"}),
    })
    with httpx.Client(transport=transport) as client:
        with pytest.raises(skills_repo.SkillsRepoError):
            skills_repo.list_skills(client=client, use_cache=False)


def test_find_skills_filters_case_insensitively():
    transport = _mock_transport({
        "/repos/android/skills/contents": httpx.Response(200, json=_contents_payload()),
    })
    with httpx.Client(transport=transport) as client:
        hits = skills_repo.find_skills("COMPOSE", client=client)
    assert [h.name for h in hits] == ["jetpack-compose"]


# ---------- add (download) unit tests --------------------------------------

def test_download_skill_extracts_only_target_subtree(tmp_path: Path):
    payload = _build_repo_tarball({
        "jetpack-compose": {
            "SKILL.md": "# Compose\n",
            "examples/foo.kt": "fun foo() {}\n",
        },
        "navigation": {"SKILL.md": "# Nav\n"},
    })
    transport = _mock_transport({
        "/repos/android/skills/tarball": httpx.Response(200, content=payload),
    })
    with httpx.Client(transport=transport) as client:
        out = skills_repo.download_skill(
            "jetpack-compose", tmp_path, client=client
        )
    assert out == tmp_path / "jetpack-compose"
    assert (out / "SKILL.md").read_text(encoding="utf-8") == "# Compose\n"
    assert (out / "examples" / "foo.kt").exists()
    # Other skills must not leak in.
    assert not (tmp_path / "navigation").exists()


def test_download_skill_replaces_existing(tmp_path: Path):
    (tmp_path / "jetpack-compose").mkdir()
    (tmp_path / "jetpack-compose" / "STALE.txt").write_text("old")

    payload = _build_repo_tarball({
        "jetpack-compose": {"SKILL.md": "fresh"},
    })
    transport = _mock_transport({
        "/repos/android/skills/tarball": httpx.Response(200, content=payload),
    })
    with httpx.Client(transport=transport) as client:
        skills_repo.download_skill("jetpack-compose", tmp_path, client=client)
    assert not (tmp_path / "jetpack-compose" / "STALE.txt").exists()
    assert (tmp_path / "jetpack-compose" / "SKILL.md").read_text() == "fresh"


def test_download_skill_unknown_name_raises(tmp_path: Path):
    payload = _build_repo_tarball({"compose": {"SKILL.md": "x"}})
    transport = _mock_transport({
        "/repos/android/skills/tarball": httpx.Response(200, content=payload),
    })
    with httpx.Client(transport=transport) as client:
        with pytest.raises(skills_repo.SkillsRepoError):
            skills_repo.download_skill("nope", tmp_path, client=client)


def test_download_skill_rejects_path_traversal_in_name(tmp_path: Path):
    transport = _mock_transport({})
    with httpx.Client(transport=transport) as client:
        with pytest.raises(skills_repo.SkillsRepoError):
            skills_repo.download_skill("../etc", tmp_path, client=client)


# ---------- remove unit tests -----------------------------------------------

def test_remove_skill_deletes_dir(tmp_path: Path):
    target = tmp_path / "compose"
    target.mkdir()
    (target / "x").write_text("y")
    assert skills_repo.remove_skill("compose", tmp_path) is True
    assert not target.exists()


def test_remove_skill_missing_returns_false(tmp_path: Path):
    assert skills_repo.remove_skill("absent", tmp_path) is False


def test_remove_skill_rejects_traversal(tmp_path: Path):
    with pytest.raises(skills_repo.SkillsRepoError):
        skills_repo.remove_skill("../etc", tmp_path)


# ---------- CLI integration tests -----------------------------------------

@pytest.fixture
def stub_list(monkeypatch: pytest.MonkeyPatch):
    def fake(upstream=skills_repo.DEFAULT_UPSTREAM, *, client=None, use_cache=True):
        return [skills_repo.Skill(name=n) for n in
                ["build", "jetpack-compose", "navigation", "play"]]
    monkeypatch.setattr(skills_repo, "list_skills", fake)
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.skills.skills_repo.list_skills",
        fake,
    )


def test_cli_list_plain(runner: CliRunner, isolated_home: Path, stub_list):
    result = runner.invoke(app, ["skills", "list"])
    assert result.exit_code == 0, result.output
    assert "jetpack-compose" in result.output
    assert "build" in result.output


def test_cli_list_json(runner: CliRunner, isolated_home: Path, stub_list):
    result = runner.invoke(app, ["skills", "list", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == [
        "build", "jetpack-compose", "navigation", "play"
    ]


def test_cli_find_match(runner: CliRunner, isolated_home: Path, stub_list):
    result = runner.invoke(app, ["skills", "find", "compose"])
    assert result.exit_code == 0, result.output
    assert "jetpack-compose" in result.output


def test_cli_find_no_match_exits_1(
    runner: CliRunner, isolated_home: Path, stub_list
):
    result = runner.invoke(app, ["skills", "find", "no_such_thing_xyz"])
    assert result.exit_code == 1


def test_cli_add_then_remove(
    runner: CliRunner, isolated_home: Path, monkeypatch: pytest.MonkeyPatch
):
    payload = _build_repo_tarball({"compose": {"SKILL.md": "hi"}})
    real_download = skills_repo.download_skill

    def fake_download(name, dest, upstream=skills_repo.DEFAULT_UPSTREAM, *, client=None):
        transport = _mock_transport({
            "/repos/android/skills/tarball": httpx.Response(200, content=payload),
        })
        with httpx.Client(transport=transport) as c:
            return real_download(name, dest, upstream, client=c)

    monkeypatch.setattr(skills_repo, "download_skill", fake_download)

    result = runner.invoke(app, ["skills", "add", "compose"])
    assert result.exit_code == 0, result.output
    assert (config.skills_dir() / "compose" / "SKILL.md").read_text() == "hi"

    result = runner.invoke(app, ["skills", "remove", "compose"])
    assert result.exit_code == 0, result.output
    assert not (config.skills_dir() / "compose").exists()


def test_cli_remove_missing_exits_1(runner: CliRunner, isolated_home: Path):
    result = runner.invoke(app, ["skills", "remove", "absent"])
    assert result.exit_code == 1
