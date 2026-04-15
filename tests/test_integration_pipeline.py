"""Integration coverage for the main scraper pipeline."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import main
from db import PostingDB


def _tier1_posting(
    *,
    posting_id: str,
    url: str,
    title: str = "Machine Learning Intern",
    description: str = "Build ML systems for search relevance.",
) -> dict:
    return {
        "posting_id": posting_id,
        "title": title,
        "description": description,
        "url": url,
        "company_slug": "openai",
        "company_name": "OpenAI",
        "skills": "Python",
        "team": "AI Platform",
    }


def test_process_postings_classifies_stores_and_dedups(tmp_path, monkeypatch) -> None:
    """A matching posting should be classified, stored, and alerted once."""
    test_db = PostingDB(str(tmp_path / "integration.db"))
    monkeypatch.setattr(main, "db", test_db)

    mock_send_alert = AsyncMock()
    monkeypatch.setattr(main, "send_alert", mock_send_alert)

    posting = {
        "posting_id": "job-123",
        "title": "Machine Learning Intern",
        "description": "Build ML systems for search relevance.",
        "url": "https://example.com/jobs/123",
        "company_slug": "acme",
        "company_name": "Acme",
        "skills": "Python",
        "team": "AI Platform",
    }

    asyncio.run(main.process_postings([posting], "jobspy"))
    asyncio.run(main.process_postings([posting], "jobspy"))

    stored = test_db.get_recent(limit=10)
    assert len(stored) == 1
    assert stored[0]["track"] == "ai_data"
    assert stored[0]["company_name"] == "Acme"
    assert stored[0]["source"] == "jobspy"
    assert stored[0]["canonical_source"] == "jobspy"
    assert stored[0]["canonical_posting_id"] == "job-123"
    mock_send_alert.assert_awaited_once()

    test_db.close()


def test_process_postings_threads_metadata_into_storage_and_alert(
    tmp_path, monkeypatch
) -> None:
    """Accepted postings should carry alert metadata through the pipeline."""
    test_db = PostingDB(str(tmp_path / "metadata.db"))
    monkeypatch.setattr(main, "db", test_db)

    mock_send_alert = AsyncMock()
    monkeypatch.setattr(main, "send_alert", mock_send_alert)

    posting = _tier1_posting(
        posting_id="ash-123",
        url="https://jobs.openai.com/careers/123?jobId=123",
        description="Build ML systems for search relevance.",
    )
    posting["skills"] = "Python, PyTorch, distributed systems"
    posting["posted_at"] = "2026-04-14T15:00:00Z"

    asyncio.run(main.process_postings([posting], "ashby"))

    stored = test_db.get_recent(limit=1)
    assert len(stored) == 1
    row = stored[0]
    assert row["source"] == "ashby"
    assert row["canonical_source"] == "ashby"
    assert row["posting_id"] == "ash-123"
    assert row["canonical_posting_id"] == "openai|https://jobs.openai.com/careers/123?jobId=123"
    assert row["tier"] == "tier_1"
    assert row["source_type"] == "direct"
    assert row["track"] == "ai_data"
    assert row["matched_keyword"] == "machine learning"
    assert row["key_skills"] == "Python, PyTorch, distributed systems"
    assert row["posted_at"] == "2026-04-14T15:00:00Z"
    assert row["first_seen_at"] > 0

    mock_send_alert.assert_awaited_once()
    alerted_posting = mock_send_alert.await_args.args[0]
    assert alerted_posting["tier"] == "tier_1"
    assert alerted_posting["source_type"] == "direct"
    assert alerted_posting["matched_keyword"] == "machine learning"
    assert alerted_posting["key_skills"] == "Python, PyTorch, distributed systems"
    assert alerted_posting["posted_at"] == "2026-04-14T15:00:00Z"
    assert alerted_posting["first_seen_at"] == row["first_seen_at"]
    assert alerted_posting["track"] == "ai_data"
    assert alerted_posting["canonical_source"] == "ashby"
    assert alerted_posting["canonical_posting_id"] == "openai|https://jobs.openai.com/careers/123?jobId=123"

    test_db.close()


def test_process_postings_fallback_first_then_preferred_later_uses_one_canonical_copy(
    tmp_path, monkeypatch
) -> None:
    """Fallback-first and preferred-later copies should collapse into one canonical record."""
    test_db = PostingDB(str(tmp_path / "tier1_accept.db"))
    monkeypatch.setattr(main, "db", test_db)

    mock_send_alert = AsyncMock()
    monkeypatch.setattr(main, "send_alert", mock_send_alert)

    fallback_posting = _tier1_posting(
        posting_id="gh-123",
        url="https://jobs.openai.com/careers/123?jobId=123&ref=github",
    )
    preferred_posting = _tier1_posting(
        posting_id="ash-999",
        url="https://jobs.openai.com/careers/123?jobId=123&utm_source=ashby",
    )

    asyncio.run(main.process_postings([fallback_posting], "github"))
    asyncio.run(main.process_postings([preferred_posting], "ashby"))

    stored = test_db.get_recent(limit=10)
    assert len(stored) == 1
    assert stored[0]["source"] == "github"
    assert stored[0]["source_type"] == "fallback"
    assert stored[0]["canonical_source"] == "ashby"
    assert stored[0]["canonical_posting_id"] == "openai|https://jobs.openai.com/careers/123?jobId=123"
    assert stored[0]["company_slug"] == "openai"
    mock_send_alert.assert_awaited_once()

    test_db.close()


def test_process_postings_preferred_first_then_fallback_keeps_preferred_copy(
    tmp_path, monkeypatch
) -> None:
    """Preferred copies should remain canonical when a fallback arrives later."""
    test_db = PostingDB(str(tmp_path / "tier1_skip.db"))
    monkeypatch.setattr(main, "db", test_db)

    mock_send_alert = AsyncMock()
    monkeypatch.setattr(main, "send_alert", mock_send_alert)

    preferred_posting = _tier1_posting(
        posting_id="ash-123",
        url="https://jobs.openai.com/careers/456?jobId=456",
    )
    fallback_posting = _tier1_posting(
        posting_id="gh-456",
        url="https://jobs.openai.com/careers/456/?jobId=456&utm_source=github",
    )

    asyncio.run(main.process_postings([preferred_posting], "ashby"))
    asyncio.run(main.process_postings([fallback_posting], "github"))

    stored = test_db.get_recent(limit=10)
    assert len(stored) == 1
    assert stored[0]["source"] == "ashby"
    assert stored[0]["source_type"] == "direct"
    assert stored[0]["canonical_source"] == "ashby"
    assert stored[0]["canonical_posting_id"] == "openai|https://jobs.openai.com/careers/456?jobId=456"
    assert stored[0]["company_slug"] == "openai"
    mock_send_alert.assert_awaited_once()

    test_db.close()


def test_process_postings_keeps_distinct_tier1_jobs_separate(tmp_path, monkeypatch) -> None:
    """Distinct tier-1 jobs should still produce distinct canonical rows."""
    test_db = PostingDB(str(tmp_path / "tier1_distinct.db"))
    monkeypatch.setattr(main, "db", test_db)

    mock_send_alert = AsyncMock()
    monkeypatch.setattr(main, "send_alert", mock_send_alert)

    first_posting = _tier1_posting(
        posting_id="gh-111",
        url="https://jobs.openai.com/careers/roles?jobId=111&utm_source=github",
    )
    second_posting = _tier1_posting(
        posting_id="gh-222",
        url="https://jobs.openai.com/careers/roles?jobId=222&utm_source=github",
        title="Software Engineer Intern",
        description="Build developer tools for platform engineering.",
    )

    asyncio.run(main.process_postings([first_posting], "github"))
    asyncio.run(main.process_postings([second_posting], "github"))

    stored = test_db.get_recent(limit=10)
    assert len(stored) == 2
    assert {row["posting_id"] for row in stored} == {"gh-111", "gh-222"}
    assert {row["canonical_posting_id"] for row in stored} == {
        "openai|https://jobs.openai.com/careers/roles?jobId=111",
        "openai|https://jobs.openai.com/careers/roles?jobId=222",
    }
    assert mock_send_alert.await_count == 2

    test_db.close()
