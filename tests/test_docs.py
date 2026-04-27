from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Optional

import httpx
import pytest
from typer.testing import CliRunner

from android_cli_mac_x86_community.cli import app
from android_cli_mac_x86_community.utils import config, docs_index, docs_kb


# ---------- helpers ---------------------------------------------------------

SAMPLE_ENTRIES = [
    (
        "android/guide/components/activities/activity-lifecycle",
        {
            "title": "Activity lifecycle",
            "short_description": "How an Activity transitions between states.",
            "keywords": "activity,lifecycle,onCreate,onResume",
            "url": "kb://android/guide/components/activities/activity-lifecycle",
            "relative_url": "android/guide/components/activities/activity-lifecycle",
        },
        "# Activity lifecycle\n\nAn Activity has onCreate, onStart, onResume...",
    ),
    (
        "android/guide/fragments/lifecycle",
        {
            "title": "Fragment Lifecycle",
            "short_description": "Lifecycle of a Fragment in Android.",
            "keywords": "fragment,lifecycle",
            "url": "kb://android/guide/fragments/lifecycle",
            "relative_url": "android/guide/fragments/lifecycle",
        },
        "# Fragment Lifecycle\n\nFragments have their own lifecycle...",
    ),
    (
        "android/topic/libraries/architecture/lifecycle",
        {
            "title": "Lifecycle-aware components",
            "short_description": "Use Lifecycle classes to manage state.",
            "keywords": "lifecycle,architecture,jetpack",
            "url": "kb://android/topic/libraries/architecture/lifecycle",
            "relative_url": "android/topic/libraries/architecture/lifecycle",
        },
        "# Lifecycle-aware components\n\nUse the new Lifecycle classes...",
    ),
]


def _build_fake_kb_zip(path: Path, entries=SAMPLE_ENTRIES) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for relpath, meta, body in entries:
            zf.writestr(relpath + ".json", json.dumps(meta))
            zf.writestr(relpath + ".md.txt", body)


def _fake_kb_zip_bytes(entries=SAMPLE_ENTRIES) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for relpath, meta, body in entries:
            zf.writestr(relpath + ".json", json.dumps(meta))
            zf.writestr(relpath + ".md.txt", body)
    return buf.getvalue()


@pytest.fixture
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect ~/.android-cli-mac-x86-community/ to a temp dir."""
    monkeypatch.setattr(config, "config_root", lambda: tmp_path / "cfg")
    return tmp_path


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ---------- docs_index unit tests ------------------------------------------

def test_index_build_and_search(tmp_path: Path):
    zip_path = tmp_path / "kb.zip"
    db_path = tmp_path / "index.sqlite3"
    _build_fake_kb_zip(zip_path)

    docs_index.ensure_index(zip_path, db_path)
    hits = docs_index.search(db_path, "Activity lifecycle")
    assert hits, "expected at least one hit"
    assert hits[0].title == "Activity lifecycle"
    assert hits[0].kb_url.startswith("kb://")


def test_index_skips_rebuild_when_zip_unchanged(tmp_path: Path):
    zip_path = tmp_path / "kb.zip"
    db_path = tmp_path / "index.sqlite3"
    _build_fake_kb_zip(zip_path)

    docs_index.ensure_index(zip_path, db_path)
    first_mtime = db_path.stat().st_mtime_ns

    # A second call with the same zip should be a no-op rebuild.
    docs_index.ensure_index(zip_path, db_path)
    assert db_path.stat().st_mtime_ns == first_mtime


def test_index_rebuild_when_zip_changes(tmp_path: Path):
    zip_path = tmp_path / "kb.zip"
    db_path = tmp_path / "index.sqlite3"
    _build_fake_kb_zip(zip_path, SAMPLE_ENTRIES[:1])
    docs_index.ensure_index(zip_path, db_path)
    assert len(docs_index.search(db_path, "lifecycle", limit=10)) == 1

    _build_fake_kb_zip(zip_path, SAMPLE_ENTRIES)
    docs_index.ensure_index(zip_path, db_path)
    assert len(docs_index.search(db_path, "lifecycle", limit=10)) == 3


def test_search_query_with_special_chars_does_not_explode(tmp_path: Path):
    zip_path = tmp_path / "kb.zip"
    db_path = tmp_path / "index.sqlite3"
    _build_fake_kb_zip(zip_path)
    docs_index.ensure_index(zip_path, db_path)
    # Quotes / parens / colons would break a raw FTS MATCH expression;
    # the escape layer should keep this as a plain phrase search.
    hits = docs_index.search(db_path, 'activity"(:lifecycle)')
    # No assertion on content — we only require it not to raise.
    assert isinstance(hits, list)


def test_fetch_returns_body_for_kb_url(tmp_path: Path):
    zip_path = tmp_path / "kb.zip"
    _build_fake_kb_zip(zip_path)
    body = docs_index.fetch(
        zip_path, "kb://android/guide/fragments/lifecycle"
    )
    assert "Fragment Lifecycle" in body


def test_fetch_rejects_non_kb_url(tmp_path: Path):
    zip_path = tmp_path / "kb.zip"
    _build_fake_kb_zip(zip_path)
    with pytest.raises(docs_index.DocsIndexError):
        docs_index.fetch(zip_path, "https://example.com/foo")


def test_fetch_missing_entry(tmp_path: Path):
    zip_path = tmp_path / "kb.zip"
    _build_fake_kb_zip(zip_path)
    with pytest.raises(docs_index.DocsIndexError):
        docs_index.fetch(zip_path, "kb://no/such/page")


# ---------- docs_kb unit tests ---------------------------------------------

def test_ensure_kb_downloads_when_missing(isolated_home: Path):
    payload = _fake_kb_zip_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        # First call: no If-None-Match header, server returns 200.
        assert "If-None-Match" not in request.headers
        return httpx.Response(200, content=payload, headers={"ETag": '"abc123"'})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        path = docs_kb.ensure_kb(client=client)

    assert path == config.docs_kb_zip_path()
    assert path.read_bytes() == payload
    assert config.docs_kb_etag_path().read_text(encoding="utf-8") == '"abc123"'


def test_ensure_kb_uses_cache_on_304(isolated_home: Path):
    # Pre-populate cache.
    config.docs_dir().mkdir(parents=True, exist_ok=True)
    config.docs_kb_zip_path().write_bytes(b"old-zip-bytes")
    config.docs_kb_etag_path().write_text('"abc123"', encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("If-None-Match") == '"abc123"'
        return httpx.Response(304)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        path = docs_kb.ensure_kb(client=client)

    assert path.read_bytes() == b"old-zip-bytes"


def test_ensure_kb_force_ignores_local_etag(isolated_home: Path):
    config.docs_dir().mkdir(parents=True, exist_ok=True)
    config.docs_kb_zip_path().write_bytes(b"old")
    config.docs_kb_etag_path().write_text('"old-etag"', encoding="utf-8")
    new_payload = _fake_kb_zip_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert "If-None-Match" not in request.headers
        return httpx.Response(200, content=new_payload, headers={"ETag": '"new"'})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        docs_kb.ensure_kb(client=client, force=True)

    assert config.docs_kb_zip_path().read_bytes() == new_payload
    assert config.docs_kb_etag_path().read_text(encoding="utf-8") == '"new"'


def test_ensure_kb_raises_on_unexpected_status(isolated_home: Path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        with pytest.raises(docs_kb.KBDownloadError):
            docs_kb.ensure_kb(client=client)


# ---------- CLI integration tests ------------------------------------------

@pytest.fixture
def stub_ensure_kb(monkeypatch: pytest.MonkeyPatch, isolated_home: Path) -> Path:
    """Skip the network and pre-seed a fake KB zip on disk."""
    config.docs_dir().mkdir(parents=True, exist_ok=True)
    zip_path = config.docs_kb_zip_path()
    _build_fake_kb_zip(zip_path)

    def fake_ensure(*, force: bool = False, client=None, url: str = ""):
        return zip_path

    monkeypatch.setattr(docs_kb, "ensure_kb", fake_ensure)
    monkeypatch.setattr(
        "android_cli_mac_x86_community.commands.docs.docs_kb.ensure_kb",
        fake_ensure,
    )
    return zip_path


def test_cli_search_prints_results(
    runner: CliRunner, stub_ensure_kb: Path
):
    result = runner.invoke(app, ["docs", "search", "Activity lifecycle"])
    assert result.exit_code == 0, result.output
    assert "Activity lifecycle" in result.output
    assert "kb://" in result.output


def test_cli_search_json_output(
    runner: CliRunner, stub_ensure_kb: Path
):
    result = runner.invoke(
        app, ["docs", "search", "Activity lifecycle", "--json"]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data and data[0]["kb_url"].startswith("kb://")


def test_cli_search_no_results_exits_1(
    runner: CliRunner, stub_ensure_kb: Path
):
    result = runner.invoke(app, ["docs", "search", "zzz_no_such_term_xyzzy"])
    assert result.exit_code == 1


def test_cli_fetch_prints_body(
    runner: CliRunner, stub_ensure_kb: Path
):
    result = runner.invoke(
        app, ["docs", "fetch", "kb://android/guide/fragments/lifecycle"]
    )
    assert result.exit_code == 0, result.output
    assert "Fragment Lifecycle" in result.output


def test_cli_fetch_unknown_kb_url_exits_1(
    runner: CliRunner, stub_ensure_kb: Path
):
    result = runner.invoke(app, ["docs", "fetch", "kb://no/such/page"])
    assert result.exit_code == 1
