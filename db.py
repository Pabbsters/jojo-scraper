"""SQLite persistence layer for tracking seen postings."""

from __future__ import annotations

import os
import sqlite3
import time
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from config import TIER1_SOURCE_PREFERENCES


_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS seen_postings (
    source        TEXT    NOT NULL,
    company_slug  TEXT    NOT NULL,
    posting_id    TEXT    NOT NULL,
    canonical_source TEXT NOT NULL DEFAULT '',
    canonical_posting_id TEXT NOT NULL DEFAULT '',
    title         TEXT    NOT NULL DEFAULT '',
    url           TEXT    NOT NULL DEFAULT '',
    track         TEXT    NOT NULL DEFAULT '',
    company_name  TEXT    NOT NULL DEFAULT '',
    skills        TEXT    NOT NULL DEFAULT '',
    comp          TEXT    NOT NULL DEFAULT '',
    team          TEXT    NOT NULL DEFAULT '',
    deadline      TEXT    NOT NULL DEFAULT '',
    tier          TEXT    NOT NULL DEFAULT '',
    source_type   TEXT    NOT NULL DEFAULT '',
    matched_keyword TEXT  NOT NULL DEFAULT '',
    key_skills    TEXT    NOT NULL DEFAULT '',
    posted_at     TEXT    NOT NULL DEFAULT '',
    first_seen_at REAL    NOT NULL DEFAULT 0,
    seen_at       REAL    NOT NULL DEFAULT 0,
    PRIMARY KEY (source, company_slug, posting_id)
)
"""

_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_seen_at ON seen_postings (seen_at)
"""

_CREATE_CANONICAL_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_seen_canonical
ON seen_postings (canonical_source, company_slug, canonical_posting_id)
"""

_CREATE_FIRST_SEEN_INDEX = """
CREATE INDEX IF NOT EXISTS idx_first_seen_at ON seen_postings (first_seen_at)
"""

_TRACKING_QUERY_PARAMS = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "ref",
    "referrer",
    "source",
    "trk",
}


class PostingDB:
    """Thin wrapper around a SQLite database of seen job postings."""

    def __init__(self, path: str = "postings.db") -> None:
        parent = os.path.dirname(os.path.abspath(path))
        os.makedirs(parent, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._migrate()

    # ── public API ─────────────────────────────────────────────────

    def is_new(self, source: str, company_slug: str, posting_id: str) -> bool:
        """Return True if this posting has never been seen."""
        cursor = self._conn.execute(
            "SELECT 1 FROM seen_postings "
            "WHERE canonical_source = ? AND company_slug = ? AND canonical_posting_id = ?",
            (source, company_slug, posting_id),
        )
        return cursor.fetchone() is None

    def mark_seen(
        self,
        source: str,
        company_slug: str,
        posting_id: str,
        title: str,
        url: str,
        track: str = "",
        company_name: str = "",
        skills: str = "",
        comp: str = "",
        team: str = "",
        deadline: str = "",
        tier: str = "",
        source_type: str = "",
        matched_keyword: str = "",
        key_skills: str = "",
        posted_at: str = "",
        canonical_source: str = "",
        canonical_posting_id: str = "",
    ) -> None:
        """Record a posting as seen (upsert)."""
        stored_skills = skills or key_skills
        stored_key_skills = key_skills or skills
        canonical_source = canonical_source or source
        canonical_posting_id = canonical_posting_id or posting_id
        seen_at = time.time()
        self._conn.execute(
            "INSERT INTO seen_postings "
            "(source, company_slug, posting_id, canonical_source, canonical_posting_id, title, url, "
            " track, company_name, skills, comp, team, deadline, "
            " tier, source_type, matched_keyword, key_skills, posted_at, first_seen_at, seen_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(canonical_source, company_slug, canonical_posting_id) DO UPDATE SET "
            "title = COALESCE(NULLIF(excluded.title, ''), seen_postings.title), "
            "url = COALESCE(NULLIF(excluded.url, ''), seen_postings.url), "
            "track = COALESCE(NULLIF(excluded.track, ''), seen_postings.track), "
            "company_name = COALESCE(NULLIF(excluded.company_name, ''), seen_postings.company_name), "
            "skills = COALESCE(NULLIF(excluded.skills, ''), seen_postings.skills), "
            "comp = COALESCE(NULLIF(excluded.comp, ''), seen_postings.comp), "
            "team = COALESCE(NULLIF(excluded.team, ''), seen_postings.team), "
            "deadline = COALESCE(NULLIF(excluded.deadline, ''), seen_postings.deadline), "
            "tier = COALESCE(NULLIF(excluded.tier, ''), seen_postings.tier), "
            "matched_keyword = COALESCE(NULLIF(excluded.matched_keyword, ''), seen_postings.matched_keyword), "
            "key_skills = COALESCE(NULLIF(excluded.key_skills, ''), seen_postings.key_skills), "
            "posted_at = COALESCE(NULLIF(excluded.posted_at, ''), seen_postings.posted_at), "
            "first_seen_at = seen_postings.first_seen_at, "
            "seen_at = excluded.seen_at",
            (
                source,
                company_slug,
                posting_id,
                canonical_source,
                canonical_posting_id,
                title,
                url,
                track,
                company_name,
                stored_skills,
                comp,
                team,
                deadline,
                tier,
                source_type,
                matched_keyword,
                stored_key_skills,
                posted_at,
                seen_at,
                seen_at,
            ),
        )
        self._conn.commit()

    def get_recent(self, limit: int = 50) -> list[dict]:
        """Return the most recent postings, newest first."""
        cursor = self._conn.execute(
            "SELECT * FROM seen_postings ORDER BY first_seen_at DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_feed_since(self, since_ts: float) -> list[dict]:
        """Return all postings seen after *since_ts* (unix timestamp)."""
        cursor = self._conn.execute(
            "SELECT * FROM seen_postings WHERE first_seen_at > ? ORDER BY first_seen_at ASC",
            (since_ts,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def close(self) -> None:
        """Close the database connection (idempotent)."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ── private ────────────────────────────────────────────────────

    def _migrate(self) -> None:
        self._conn.execute(_CREATE_TABLE)
        self._ensure_columns(
            {
                "canonical_source": "TEXT NOT NULL DEFAULT ''",
                "canonical_posting_id": "TEXT NOT NULL DEFAULT ''",
                "tier": "TEXT NOT NULL DEFAULT ''",
                "source_type": "TEXT NOT NULL DEFAULT ''",
                "matched_keyword": "TEXT NOT NULL DEFAULT ''",
                "key_skills": "TEXT NOT NULL DEFAULT ''",
                "posted_at": "TEXT NOT NULL DEFAULT ''",
                "first_seen_at": "REAL NOT NULL DEFAULT 0",
            }
        )
        self._conn.execute(
            "UPDATE seen_postings SET first_seen_at = seen_at "
            "WHERE first_seen_at = 0 OR first_seen_at IS NULL"
        )
        self._backfill_canonical_identities()
        self._collapse_duplicate_canonical_identities()
        self._conn.execute(_CREATE_CANONICAL_INDEX)
        self._conn.execute(_CREATE_INDEX)
        self._conn.execute(_CREATE_FIRST_SEEN_INDEX)
        self._conn.commit()

    def _backfill_canonical_identities(self) -> None:
        rows = self._conn.execute(
            "SELECT rowid, source, company_slug, posting_id, url, canonical_source, canonical_posting_id "
            "FROM seen_postings "
            "WHERE canonical_source = '' OR canonical_posting_id = ''"
        ).fetchall()
        for row in rows:
            canonical_source, canonical_posting_id = _canonical_identity_for_posting(
                row["source"],
                row["company_slug"],
                row["posting_id"],
                row["url"],
            )
            self._conn.execute(
                "UPDATE seen_postings SET canonical_source = ?, canonical_posting_id = ? "
                "WHERE rowid = ?",
                (canonical_source, canonical_posting_id, row["rowid"]),
            )

    def _collapse_duplicate_canonical_identities(self) -> None:
        rows = self._conn.execute(
            "SELECT rowid, source, company_slug, posting_id, canonical_source, "
            "canonical_posting_id, first_seen_at, seen_at "
            "FROM seen_postings "
            "ORDER BY first_seen_at ASC, seen_at ASC, rowid ASC"
        ).fetchall()

        grouped: dict[tuple[str, str, str], list[sqlite3.Row]] = {}
        for row in rows:
            canonical_source = row["canonical_source"] or row["source"]
            canonical_posting_id = row["canonical_posting_id"] or row["posting_id"]
            key = (canonical_source, row["company_slug"], canonical_posting_id)
            grouped.setdefault(key, []).append(row)

        for (canonical_source, _company_slug, canonical_posting_id), group in grouped.items():
            if len(group) < 2:
                continue

            winner = self._choose_canonical_winner(group, canonical_source)
            first_seen_at = min(_row_first_seen_at(row) for row in group)
            seen_at = max(_row_seen_at(row) for row in group)

            self._conn.execute(
                "UPDATE seen_postings SET canonical_source = ?, canonical_posting_id = ?, "
                "first_seen_at = ?, seen_at = ? WHERE rowid = ?",
                (canonical_source, canonical_posting_id, first_seen_at, seen_at, winner["rowid"]),
            )

            loser_rowids = [row["rowid"] for row in group if row["rowid"] != winner["rowid"]]
            self._conn.executemany(
                "DELETE FROM seen_postings WHERE rowid = ?",
                [(rowid,) for rowid in loser_rowids],
            )

    @staticmethod
    def _choose_canonical_winner(
        rows: list[sqlite3.Row],
        canonical_source: str,
    ) -> sqlite3.Row:
        preferred = [row for row in rows if row["source"] == canonical_source]
        candidates = preferred or rows
        return min(
            candidates,
            key=lambda row: (
                _row_first_seen_at(row),
                _row_seen_at(row),
                row["rowid"],
            ),
        )

    def _ensure_columns(self, columns: dict[str, str]) -> None:
        existing = {
            row["name"]
            for row in self._conn.execute("PRAGMA table_info(seen_postings)").fetchall()
        }
        for name, ddl in columns.items():
            if name not in existing:
                self._conn.execute(f"ALTER TABLE seen_postings ADD COLUMN {name} {ddl}")


def _normalize_job_url(url: str) -> str:
    """Return a conservative canonical job URL with tracking params removed."""
    raw = url.strip()
    if not raw:
        return ""

    parsed = urlsplit(raw)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not _is_tracking_param(key)
    ]
    query_items.sort()
    query = urlencode(query_items, doseq=True)
    return urlunsplit((scheme, netloc, path, query, ""))


def _is_tracking_param(name: str) -> bool:
    lowered = name.lower()
    return lowered.startswith("utm_") or lowered in _TRACKING_QUERY_PARAMS


def _canonical_identity_for_posting(
    source: str,
    company_slug: str,
    posting_id: str,
    url: str,
) -> tuple[str, str]:
    """Return the canonical dedupe identity for a posting."""
    preferred = TIER1_SOURCE_PREFERENCES.get(company_slug)
    if preferred is None:
        return source, posting_id

    canonical_posting_id = _normalize_job_url(url) or posting_id
    if canonical_posting_id:
        canonical_posting_id = f"{company_slug}|{canonical_posting_id}"
    return preferred["preferred_source"], canonical_posting_id


def _row_first_seen_at(row: sqlite3.Row) -> float:
    value = row["first_seen_at"]
    return float(value) if value not in (None, "") else 0.0


def _row_seen_at(row: sqlite3.Row) -> float:
    value = row["seen_at"]
    return float(value) if value not in (None, "") else 0.0
