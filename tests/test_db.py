"""Tests for the PostingDB persistence layer."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import time

import pytest

from db import PostingDB
from db import _normalize_job_url


@pytest.fixture()
def db_path(tmp_path):
    """Return a temporary database file path."""
    return str(tmp_path / "test_postings.db")


@pytest.fixture()
def db(db_path):
    """Create a fresh PostingDB instance and close it after the test."""
    database = PostingDB(path=db_path)
    yield database
    database.close()


# ── Table creation ─────────────────────────────────────────────────────

class TestTableCreation:

    def test_creates_database_file(self, db, db_path):
        assert os.path.exists(db_path)

    def test_table_exists(self, db):
        cursor = db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='seen_postings'"
        )
        assert cursor.fetchone() is not None

    def test_index_exists(self, db):
        cursor = db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_seen_at'"
        )
        assert cursor.fetchone() is not None


# ── is_new / mark_seen ────────────────────────────────────────────────

class TestIsNewAndMarkSeen:

    def test_new_posting_is_new(self, db):
        assert db.is_new("greenhouse", "citadel", "12345") is True

    def test_after_mark_seen_not_new(self, db):
        db.mark_seen("greenhouse", "citadel", "12345", "SWE Intern", "https://example.com")
        assert db.is_new("greenhouse", "citadel", "12345") is False

    def test_different_posting_still_new(self, db):
        db.mark_seen("greenhouse", "citadel", "12345", "SWE Intern", "https://example.com")
        assert db.is_new("greenhouse", "citadel", "99999") is True

    def test_different_source_still_new(self, db):
        db.mark_seen("greenhouse", "citadel", "12345", "SWE Intern", "https://example.com")
        assert db.is_new("ashby", "citadel", "12345") is True

    def test_duplicate_mark_seen_no_error(self, db):
        db.mark_seen("greenhouse", "citadel", "12345", "SWE Intern", "https://example.com")
        # Should not raise on duplicate
        db.mark_seen("greenhouse", "citadel", "12345", "SWE Intern", "https://example.com")
        assert db.is_new("greenhouse", "citadel", "12345") is False


# ── mark_seen with optional fields ───────────────────────────────────

class TestMarkSeenOptionalFields:

    def test_all_optional_fields_stored(self, db):
        before = time.time()
        db.mark_seen(
            source="greenhouse",
            company_slug="citadel",
            posting_id="100",
            title="ML Engineer",
            url="https://example.com/100",
            track="ai_data",
            company_name="Citadel",
            skills="Python, PyTorch",
            comp="$150k",
            team="Quant Research",
            deadline="2026-06-01",
            tier="tier_1",
            source_type="direct",
            matched_keyword="machine learning",
            key_skills="Python, PyTorch, ML",
            posted_at="2026-05-30T12:00:00Z",
        )
        rows = db.get_recent(limit=1)
        assert len(rows) == 1
        row = rows[0]
        assert row["track"] == "ai_data"
        assert row["company_name"] == "Citadel"
        assert row["skills"] == "Python, PyTorch"
        assert row["comp"] == "$150k"
        assert row["team"] == "Quant Research"
        assert row["deadline"] == "2026-06-01"
        assert row["tier"] == "tier_1"
        assert row["source_type"] == "direct"
        assert row["matched_keyword"] == "machine learning"
        assert row["key_skills"] == "Python, PyTorch, ML"
        assert row["posted_at"] == "2026-05-30T12:00:00Z"
        assert row["first_seen_at"] >= before
        assert row["first_seen_at"] <= time.time()

    def test_duplicate_mark_seen_preserves_existing_metadata(self, db):
        db.mark_seen(
            source="greenhouse",
            company_slug="citadel",
            posting_id="200",
            title="ML Engineer",
            url="https://example.com/200",
            track="ai_data",
            company_name="Citadel",
            skills="Python, PyTorch",
            comp="$150k",
            team="Quant Research",
            deadline="2026-06-01",
            tier="tier_1",
            source_type="direct",
            matched_keyword="machine learning",
            key_skills="Python, PyTorch, ML",
            posted_at="2026-05-30T12:00:00Z",
        )
        original = db.get_recent(limit=1)[0]

        time.sleep(0.05)
        db.mark_seen("greenhouse", "citadel", "200", "ML Engineer", "https://example.com/200")

        rows = db.get_recent(limit=1)
        assert len(rows) == 1
        row = rows[0]
        assert row["source"] == "greenhouse"
        assert row["canonical_source"] == "greenhouse"
        assert row["canonical_posting_id"] == "200"
        assert row["tier"] == original["tier"]
        assert row["source_type"] == original["source_type"]
        assert row["matched_keyword"] == original["matched_keyword"]
        assert row["key_skills"] == original["key_skills"]
        assert row["posted_at"] == original["posted_at"]
        assert row["first_seen_at"] == original["first_seen_at"]

    def test_duplicate_mark_seen_preserves_actual_source_provenance(self, db):
        db.mark_seen(
            source="github",
            company_slug="openai",
            posting_id="fallback-1",
            title="ML Intern",
            url="https://jobs.openai.com/careers/123?utm_source=github",
            source_type="fallback",
        )
        db.mark_seen(
            source="github",
            company_slug="openai",
            posting_id="fallback-1",
            title="ML Intern",
            url="https://jobs.openai.com/careers/123?utm_source=github",
            source_type="direct",
        )

        row = db.get_recent(limit=1)[0]
        assert row["source"] == "github"
        assert row["source_type"] == "fallback"
        assert row["canonical_source"] == "github"
        assert row["canonical_posting_id"] == "fallback-1"


class TestLegacyBackfill:

    def test_backfills_canonical_identity_for_legacy_tier1_rows(self, db_path):
        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE seen_postings (
                source TEXT NOT NULL,
                company_slug TEXT NOT NULL,
                posting_id TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                track TEXT NOT NULL DEFAULT '',
                company_name TEXT NOT NULL DEFAULT '',
                skills TEXT NOT NULL DEFAULT '',
                comp TEXT NOT NULL DEFAULT '',
                team TEXT NOT NULL DEFAULT '',
                deadline TEXT NOT NULL DEFAULT '',
                seen_at REAL NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            INSERT INTO seen_postings (
                source, company_slug, posting_id, title, url, seen_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "github",
                "openai",
                "legacy-1",
                "Machine Learning Intern",
                "https://jobs.openai.com/careers/123?utm_source=github&ref=jobs",
                time.time() - 10,
            ),
        )
        conn.commit()
        conn.close()

        database = PostingDB(path=db_path)
        rows = database.get_recent(limit=1)
        assert len(rows) == 1
        row = rows[0]
        assert row["source"] == "github"
        assert row["canonical_source"] == "ashby"
        assert row["canonical_posting_id"] == "openai|https://jobs.openai.com/careers/123"
        assert row["first_seen_at"] == row["seen_at"]
        assert database.is_new(
            "ashby",
            "openai",
            "openai|https://jobs.openai.com/careers/123",
        ) is False
        database.close()

    def test_collapses_duplicate_legacy_rows_without_startup_failure(self, db_path):
        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE seen_postings (
                source TEXT NOT NULL,
                company_slug TEXT NOT NULL,
                posting_id TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                track TEXT NOT NULL DEFAULT '',
                company_name TEXT NOT NULL DEFAULT '',
                skills TEXT NOT NULL DEFAULT '',
                comp TEXT NOT NULL DEFAULT '',
                team TEXT NOT NULL DEFAULT '',
                deadline TEXT NOT NULL DEFAULT '',
                seen_at REAL NOT NULL DEFAULT 0
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO seen_postings (
                source, company_slug, posting_id, title, url, seen_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "github",
                    "openai",
                    "legacy-gh",
                    "Machine Learning Intern",
                    "https://jobs.openai.com/careers/123?ref=github&utm_source=github",
                    100.0,
                ),
                (
                    "ashby",
                    "openai",
                    "legacy-ash",
                    "Machine Learning Intern",
                    "https://jobs.openai.com/careers/123?utm_source=ashby&ref=share",
                    200.0,
                ),
            ],
        )
        conn.commit()
        conn.close()

        database = PostingDB(path=db_path)
        rows = database.get_recent(limit=10)
        assert len(rows) == 1
        row = rows[0]
        assert row["source"] == "ashby"
        assert row["canonical_source"] == "ashby"
        assert row["canonical_posting_id"] == "openai|https://jobs.openai.com/careers/123"
        assert row["first_seen_at"] == 100.0
        assert row["seen_at"] == 200.0
        assert database.is_new(
            "ashby",
            "openai",
            "openai|https://jobs.openai.com/careers/123",
        ) is False
        database.close()


class TestNormalizeJobUrl:

    def test_query_parameter_order_does_not_affect_canonical_url(self):
        left = _normalize_job_url(
            "https://jobs.openai.com/careers/123?jobId=123&utm_source=github&ref=share"
        )
        right = _normalize_job_url(
            "https://jobs.openai.com/careers/123?ref=share&jobId=123&utm_source=github"
        )
        assert left == right
        assert left == "https://jobs.openai.com/careers/123?jobId=123"


# ── get_recent ────────────────────────────────────────────────────────

class TestGetRecent:

    def test_empty_db_returns_empty(self, db):
        assert db.get_recent() == []

    def test_returns_dicts(self, db):
        db.mark_seen("gh", "citadel", "1", "Title", "https://url")
        rows = db.get_recent(limit=1)
        assert isinstance(rows, list)
        assert isinstance(rows[0], dict)

    def test_respects_limit(self, db):
        for i in range(10):
            db.mark_seen("gh", "citadel", str(i), f"Title {i}", f"https://url/{i}")
        assert len(db.get_recent(limit=3)) == 3

    def test_ordered_by_seen_at_desc(self, db):
        db.mark_seen("gh", "a", "1", "First", "https://url/1")
        time.sleep(0.05)
        db.mark_seen("gh", "b", "2", "Second", "https://url/2")
        rows = db.get_recent(limit=2)
        assert rows[0]["title"] == "Second"
        assert rows[1]["title"] == "First"


# ── get_feed_since ────────────────────────────────────────────────────

class TestGetFeedSince:

    def test_returns_only_recent(self, db):
        db.mark_seen("gh", "a", "1", "Old", "https://url/1")
        cutoff = time.time()
        time.sleep(0.05)
        db.mark_seen("gh", "b", "2", "New", "https://url/2")
        rows = db.get_feed_since(cutoff)
        assert len(rows) == 1
        assert rows[0]["title"] == "New"

    def test_empty_when_none_since(self, db):
        db.mark_seen("gh", "a", "1", "Old", "https://url/1")
        rows = db.get_feed_since(time.time() + 100)
        assert rows == []

    def test_preserves_metadata_fields(self, db):
        db.mark_seen(
            source="gh",
            company_slug="a",
            posting_id="1",
            title="Fresh Grad ML",
            url="https://url/1",
            tier="tier_1",
            source_type="direct",
            matched_keyword="ml",
            key_skills="python, ml",
            posted_at="2026-04-14T15:00:00Z",
        )
        rows = db.get_feed_since(0)
        assert len(rows) == 1
        row = rows[0]
        assert row["tier"] == "tier_1"
        assert row["source_type"] == "direct"
        assert row["matched_keyword"] == "ml"
        assert row["key_skills"] == "python, ml"
        assert row["posted_at"] == "2026-04-14T15:00:00Z"
        assert isinstance(row["first_seen_at"], float)


# ── close ─────────────────────────────────────────────────────────────

class TestClose:

    def test_close_is_idempotent(self, db):
        db.close()
        db.close()  # Should not raise
