"""SQLite FTS5 index over the KB zip.

Each KB entry is a pair: `<path>.json` (metadata) + `<path>.md.txt` (body).
We index `(title, keywords, short_description, body)` per entry and use
the zip's SHA-256 as a sentinel — when the zip changes, the index is
rebuilt from scratch.

`fetch(kb_url)` reads the body straight from the cached zip; no DB hit.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

KB_URL_PREFIX = "kb://"
META_TABLE_DDL = (
    "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)"
)
DOCS_TABLE_DDL = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5("
    "kb_url UNINDEXED, title, keywords, short_description, body)"
)


class DocsIndexError(RuntimeError):
    pass


@dataclass(frozen=True)
class SearchHit:
    kb_url: str
    title: str
    short_description: str

    def to_dict(self) -> dict:
        return {
            "kb_url": self.kb_url,
            "title": self.title,
            "short_description": self.short_description,
        }


def _zip_hash(zip_path: Path) -> str:
    h = hashlib.sha256()
    with zip_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_entries(zf: zipfile.ZipFile) -> Iterator[tuple[str, dict, str]]:
    """Yield (relative_path, meta_dict, body_text) for each KB entry.

    Entries without both a `.json` and matching `.md.txt` are skipped so a
    malformed zip doesn't abort the whole rebuild.
    """
    json_names = [n for n in zf.namelist() if n.endswith(".json")]
    for jname in json_names:
        base = jname[: -len(".json")]
        body_name = base + ".md.txt"
        try:
            meta_raw = zf.read(jname).decode("utf-8", errors="replace")
            meta = json.loads(meta_raw)
        except (KeyError, json.JSONDecodeError):
            continue
        try:
            body = zf.read(body_name).decode("utf-8", errors="replace")
        except KeyError:
            body = ""
        yield base, meta, body


def _read_meta(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row[0] if row else None


def ensure_index(zip_path: Path, db_path: Path) -> Path:
    """Build (or reuse) the FTS index for `zip_path`. Returns `db_path`.

    Reuse when the stored zip hash matches; otherwise drop & rebuild.
    """
    if not zip_path.exists():
        raise DocsIndexError(f"KB zip not found: {zip_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    current_hash = _zip_hash(zip_path)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(META_TABLE_DDL)
        stored = _read_meta(conn, "zip_hash")
        if stored == current_hash:
            # Sanity check: docs table exists and is non-empty.
            try:
                count = conn.execute("SELECT count(*) FROM docs").fetchone()[0]
            except sqlite3.OperationalError:
                count = 0
            if count > 0:
                return db_path

        conn.execute("DROP TABLE IF EXISTS docs")
        conn.execute(DOCS_TABLE_DDL)
        with zipfile.ZipFile(zip_path) as zf:
            rows = []
            for relpath, meta, body in _iter_entries(zf):
                kb_url = meta.get("url") or (KB_URL_PREFIX + relpath)
                title = meta.get("title", "") or ""
                keywords = meta.get("keywords", "") or ""
                short = meta.get("short_description", "") or ""
                rows.append((kb_url, title, keywords, short, body))
            conn.executemany(
                "INSERT INTO docs(kb_url, title, keywords, short_description, body)"
                " VALUES (?, ?, ?, ?, ?)",
                rows,
            )
        conn.execute(
            "INSERT INTO meta(key, value) VALUES('zip_hash', ?)"
            " ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (current_hash,),
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def _escape_fts(query: str) -> str:
    """Escape a free-text query for FTS5 MATCH.

    FTS5 treats unquoted strings as a column-filter / operator language;
    wrapping each whitespace token in double quotes turns it into a plain
    phrase search and disables the special syntax safely.
    """
    tokens = [t for t in query.split() if t]
    if not tokens:
        return '""'
    quoted = ['"' + t.replace('"', '""') + '"' for t in tokens]
    return " ".join(quoted)


def search(db_path: Path, query: str, *, limit: int = 10) -> list[SearchHit]:
    if not db_path.exists():
        raise DocsIndexError(f"index db not found: {db_path}")
    fts_query = _escape_fts(query)
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT kb_url, title, short_description FROM docs"
            " WHERE docs MATCH ? ORDER BY rank LIMIT ?",
            (fts_query, limit),
        ).fetchall()
    finally:
        conn.close()
    return [SearchHit(kb_url=r[0], title=r[1], short_description=r[2]) for r in rows]


def fetch(zip_path: Path, kb_url: str) -> str:
    """Resolve a `kb://...` URL to the entry's `.md.txt` body in the zip."""
    if not kb_url.startswith(KB_URL_PREFIX):
        raise DocsIndexError(
            f"expected kb:// URL, got: {kb_url!r}"
        )
    relpath = kb_url[len(KB_URL_PREFIX):].strip("/")
    body_name = relpath + ".md.txt"
    if not zip_path.exists():
        raise DocsIndexError(f"KB zip not found: {zip_path}")
    with zipfile.ZipFile(zip_path) as zf:
        try:
            return zf.read(body_name).decode("utf-8", errors="replace")
        except KeyError:
            raise DocsIndexError(f"entry not found in KB: {kb_url}") from None
