"""Integration coverage for the main scraper pipeline."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import main
from db import PostingDB


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
    mock_send_alert.assert_awaited_once()

    test_db.close()
