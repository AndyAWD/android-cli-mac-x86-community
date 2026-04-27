"""Knowledge Base zip download with HTTP ETag caching.

Mirrors the upstream `android docs` mechanism: pull a public KB zip from
Google's CDN and use an ETag sentinel for freshness so we don't re-download
on every search.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import httpx

from . import config

KB_URL = "https://dl.google.com/dac/dac_kb.zip"
DEFAULT_TIMEOUT = 60.0


class KBDownloadError(RuntimeError):
    pass


def _read_local_etag(etag_path: Path) -> Optional[str]:
    if not etag_path.exists():
        return None
    text = etag_path.read_text(encoding="utf-8").strip()
    return text or None


def ensure_kb(
    *,
    force: bool = False,
    client: Optional[httpx.Client] = None,
    url: str = KB_URL,
) -> Path:
    """Ensure a fresh local copy of the KB zip exists; return its path.

    On a hit (304 Not Modified) the cached zip is reused. On 200 the zip and
    etag file are atomically replaced. `force=True` ignores the local etag.
    """
    config.docs_dir().mkdir(parents=True, exist_ok=True)
    zip_path = config.docs_kb_zip_path()
    etag_path = config.docs_kb_etag_path()

    headers: dict[str, str] = {}
    if not force and zip_path.exists():
        local_etag = _read_local_etag(etag_path)
        if local_etag:
            headers["If-None-Match"] = local_etag

    owns_client = client is None
    if owns_client:
        client = httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True)
    try:
        resp = client.get(url, headers=headers)
    finally:
        if owns_client:
            client.close()

    if resp.status_code == 304 and zip_path.exists():
        return zip_path
    if resp.status_code != 200:
        raise KBDownloadError(
            f"unexpected status {resp.status_code} fetching {url}"
        )

    # Atomic replace via sibling temp files so a crash mid-write doesn't
    # leave a half-written zip the indexer will choke on.
    tmp_zip = zip_path.with_suffix(zip_path.suffix + ".part")
    tmp_zip.write_bytes(resp.content)
    tmp_zip.replace(zip_path)

    remote_etag = resp.headers.get("ETag", "")
    if remote_etag:
        tmp_etag = etag_path.with_suffix(etag_path.suffix + ".part")
        tmp_etag.write_text(remote_etag, encoding="utf-8")
        tmp_etag.replace(etag_path)
    elif etag_path.exists():
        etag_path.unlink()

    return zip_path
