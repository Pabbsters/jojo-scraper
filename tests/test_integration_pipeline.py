"""Integration coverage for the main scraper pipeline."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import main
from db import PostingDB


def _tier1_posting(
    *,
    posting_id: str,
    url: str,
    title: str = "Machine Learning Intern - Summer 2026",
    description: str = "Build ML systems for search relevance in the US.",
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
        "location": "San Francisco, CA, United States",
    }


def _recent_timestamp() -> str:
    return "2026-04-14T15:00:00Z"


def _run_process(
    posting: dict,
    source: str,
    tmp_path,
    monkeypatch,
) -> tuple[PostingDB, AsyncMock]:
    test_db = PostingDB(str(tmp_path / f"{source}.db"))
    monkeypatch.setattr(main, "db", test_db)
    mock_send_alert = AsyncMock()
    monkeypatch.setattr(main, "send_alert", mock_send_alert)
    asyncio.run(
        main.process_postings(
            [posting],
            source,
            now=datetime(2026, 4, 15, 18, 0, tzinfo=UTC),
        )
    )
    return test_db, mock_send_alert


def test_process_postings_classifies_stores_and_dedups(tmp_path, monkeypatch) -> None:
    """A matching posting should be classified, stored, and alerted once."""
    test_db = PostingDB(str(tmp_path / "integration.db"))
    monkeypatch.setattr(main, "db", test_db)

    mock_send_alert = AsyncMock()
    monkeypatch.setattr(main, "send_alert", mock_send_alert)

    posting = _tier1_posting(
        posting_id="job-123",
        url="https://jobs.openai.com/careers/123?jobId=123",
    )
    posting["posted_at"] = _recent_timestamp()

    asyncio.run(
        main.process_postings(
            [posting],
            "ashby",
            now=datetime(2026, 4, 15, 18, 0, tzinfo=UTC),
        )
    )
    asyncio.run(
        main.process_postings(
            [posting],
            "ashby",
            now=datetime(2026, 4, 15, 18, 0, tzinfo=UTC),
        )
    )

    stored = test_db.get_recent(limit=10)
    assert len(stored) == 1
    assert stored[0]["track"] == "ai_data"
    assert stored[0]["company_name"] == "OpenAI"
    assert stored[0]["source"] == "ashby"
    assert stored[0]["canonical_source"] == "ashby"
    assert stored[0]["canonical_posting_id"] == "openai|https://jobs.openai.com/careers/123?jobId=123"
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

    asyncio.run(
        main.process_postings(
            [posting],
            "ashby",
            now=datetime(2026, 4, 15, 18, 0, tzinfo=UTC),
        )
    )

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


def test_process_postings_keeps_distinct_tier1_jobs_separate(tmp_path, monkeypatch) -> None:
    """Distinct tier-1 jobs should still produce distinct canonical rows."""
    test_db = PostingDB(str(tmp_path / "tier1_distinct.db"))
    monkeypatch.setattr(main, "db", test_db)

    mock_send_alert = AsyncMock()
    monkeypatch.setattr(main, "send_alert", mock_send_alert)

    first_posting = _tier1_posting(
        posting_id="ash-111",
        url="https://jobs.openai.com/careers/roles?jobId=111",
    )
    second_posting = _tier1_posting(
        posting_id="ash-222",
        url="https://jobs.openai.com/careers/roles?jobId=222",
        title="Software Engineer Intern - Summer 2026",
        description="Build developer tools for platform engineering in the United States.",
    )
    first_posting["posted_at"] = _recent_timestamp()
    second_posting["posted_at"] = _recent_timestamp()

    asyncio.run(
        main.process_postings(
            [first_posting],
            "ashby",
            now=datetime(2026, 4, 15, 18, 0, tzinfo=UTC),
        )
    )
    asyncio.run(
        main.process_postings(
            [second_posting],
            "ashby",
            now=datetime(2026, 4, 15, 18, 0, tzinfo=UTC),
        )
    )

    stored = test_db.get_recent(limit=10)
    assert len(stored) == 2
    assert {row["posting_id"] for row in stored} == {"ash-111", "ash-222"}
    assert {row["canonical_posting_id"] for row in stored} == {
        "openai|https://jobs.openai.com/careers/roles?jobId=111",
        "openai|https://jobs.openai.com/careers/roles?jobId=222",
    }
    assert mock_send_alert.await_count == 2

    test_db.close()


def test_process_postings_rejects_non_direct_source(tmp_path, monkeypatch) -> None:
    posting = _tier1_posting(
        posting_id="gh-123",
        url="https://jobs.openai.com/careers/123?jobId=123&ref=github",
    )
    posting["posted_at"] = _recent_timestamp()
    test_db, mock_send_alert = _run_process(posting, "github", tmp_path, monkeypatch)

    assert test_db.get_recent(limit=10) == []
    mock_send_alert.assert_not_awaited()
    test_db.close()


def test_process_postings_rejects_non_target_company(tmp_path, monkeypatch) -> None:
    posting = _tier1_posting(
        posting_id="fig-123",
        url="https://jobs.example.com/123",
    )
    posting["company_slug"] = "figma"
    posting["company_name"] = "Figma"
    posting["posted_at"] = _recent_timestamp()
    test_db, mock_send_alert = _run_process(posting, "greenhouse", tmp_path, monkeypatch)

    assert test_db.get_recent(limit=10) == []
    mock_send_alert.assert_not_awaited()
    test_db.close()


def test_process_postings_requires_trustworthy_posted_at(tmp_path, monkeypatch) -> None:
    posting = _tier1_posting(
        posting_id="ash-124",
        url="https://jobs.openai.com/careers/124?jobId=124",
    )
    test_db, mock_send_alert = _run_process(posting, "ashby", tmp_path, monkeypatch)

    assert test_db.get_recent(limit=10) == []
    mock_send_alert.assert_not_awaited()
    test_db.close()


def test_process_postings_rejects_stale_posting(tmp_path, monkeypatch) -> None:
    posting = _tier1_posting(
        posting_id="ash-125",
        url="https://jobs.openai.com/careers/125?jobId=125",
    )
    posting["posted_at"] = "2026-04-10T10:00:00Z"
    test_db, mock_send_alert = _run_process(posting, "ashby", tmp_path, monkeypatch)

    assert test_db.get_recent(limit=10) == []
    mock_send_alert.assert_not_awaited()
    test_db.close()


def test_process_postings_rejects_summer_non_us_role(tmp_path, monkeypatch) -> None:
    posting = _tier1_posting(
        posting_id="ash-126",
        url="https://jobs.openai.com/careers/126?jobId=126",
    )
    posting["location"] = "Toronto, Ontario, Canada"
    posting["posted_at"] = _recent_timestamp()
    test_db, mock_send_alert = _run_process(posting, "ashby", tmp_path, monkeypatch)

    assert test_db.get_recent(limit=10) == []
    mock_send_alert.assert_not_awaited()
    test_db.close()


def test_process_postings_accepts_spring_remote_role(tmp_path, monkeypatch) -> None:
    posting = _tier1_posting(
        posting_id="ash-127",
        url="https://jobs.openai.com/careers/127?jobId=127",
        title="ML Engineer Intern - Spring 2026",
        description="Remote internship building model training systems.",
    )
    posting["location"] = "Remote - United States"
    posting["posted_at"] = _recent_timestamp()
    test_db, mock_send_alert = _run_process(posting, "ashby", tmp_path, monkeypatch)

    stored = test_db.get_recent(limit=10)
    assert len(stored) == 1
    assert stored[0]["company_slug"] == "openai"
    mock_send_alert.assert_awaited_once()
    test_db.close()


def test_process_postings_rejects_fall_non_remote_role(tmp_path, monkeypatch) -> None:
    posting = _tier1_posting(
        posting_id="ash-128",
        url="https://jobs.openai.com/careers/128?jobId=128",
        title="ML Engineer Intern - Fall 2026",
        description="Onsite internship building inference systems.",
    )
    posting["location"] = "Seattle, WA, United States"
    posting["posted_at"] = _recent_timestamp()
    test_db, mock_send_alert = _run_process(posting, "ashby", tmp_path, monkeypatch)

    assert test_db.get_recent(limit=10) == []
    mock_send_alert.assert_not_awaited()
    test_db.close()


def test_process_postings_rejects_non_internship_style_role(tmp_path, monkeypatch) -> None:
    posting = _tier1_posting(
        posting_id="ash-129",
        url="https://jobs.openai.com/careers/129?jobId=129",
        title="Software Engineer New Grad - Summer 2026",
        description="Bachelor's degree in computer science required.",
    )
    posting["posted_at"] = _recent_timestamp()
    test_db, mock_send_alert = _run_process(posting, "ashby", tmp_path, monkeypatch)

    assert test_db.get_recent(limit=10) == []
    mock_send_alert.assert_not_awaited()
    test_db.close()


def test_process_postings_accepts_winter_remote_role(tmp_path, monkeypatch) -> None:
    posting = _tier1_posting(
        posting_id="ash-130",
        url="https://jobs.openai.com/careers/130?jobId=130",
        title="Machine Learning Intern - Winter 2026",
        description="Remote internship on model evaluation and search systems.",
    )
    posting["location"] = "Remote"
    posting["posted_at"] = _recent_timestamp()
    test_db, mock_send_alert = _run_process(posting, "ashby", tmp_path, monkeypatch)

    assert len(test_db.get_recent(limit=10)) == 1
    mock_send_alert.assert_awaited_once()
    test_db.close()


def test_process_postings_accepts_winter_us_in_person_role(tmp_path, monkeypatch) -> None:
    posting = _tier1_posting(
        posting_id="ash-131",
        url="https://jobs.openai.com/careers/131?jobId=131",
        title="Machine Learning Intern - Winter 2026",
        description="Onsite internship building inference systems in the United States.",
    )
    posting["location"] = "Seattle, WA, United States"
    posting["posted_at"] = _recent_timestamp()
    test_db, mock_send_alert = _run_process(posting, "ashby", tmp_path, monkeypatch)

    assert len(test_db.get_recent(limit=10)) == 1
    mock_send_alert.assert_awaited_once()
    test_db.close()


def test_process_postings_rejects_winter_non_us_non_remote_role(tmp_path, monkeypatch) -> None:
    posting = _tier1_posting(
        posting_id="ash-132",
        url="https://jobs.openai.com/careers/132?jobId=132",
        title="AI Systems Intern - Winter 2026",
        description="Onsite internship building inference systems.",
    )
    posting["location"] = "Toronto, Ontario, Canada"
    posting["posted_at"] = _recent_timestamp()
    test_db, mock_send_alert = _run_process(posting, "ashby", tmp_path, monkeypatch)

    assert test_db.get_recent(limit=10) == []
    mock_send_alert.assert_not_awaited()
    test_db.close()


def test_process_postings_accepts_summer_2027_us_role(tmp_path, monkeypatch) -> None:
    posting = _tier1_posting(
        posting_id="ash-133",
        url="https://jobs.openai.com/careers/133?jobId=133",
        title="Machine Learning Intern - Summer 2027",
        description="Onsite internship building search systems.",
    )
    posting["location"] = "New York, NY, United States"
    posting["posted_at"] = _recent_timestamp()
    test_db, mock_send_alert = _run_process(posting, "ashby", tmp_path, monkeypatch)

    assert len(test_db.get_recent(limit=10)) == 1
    mock_send_alert.assert_awaited_once()
    test_db.close()


def test_process_postings_rejects_summer_2027_non_us_role(tmp_path, monkeypatch) -> None:
    posting = _tier1_posting(
        posting_id="ash-134",
        url="https://jobs.openai.com/careers/134?jobId=134",
        title="Machine Learning Intern - Summer 2027",
        description="Onsite internship building search systems.",
    )
    posting["location"] = "London, United Kingdom"
    posting["posted_at"] = _recent_timestamp()
    test_db, mock_send_alert = _run_process(posting, "ashby", tmp_path, monkeypatch)

    assert test_db.get_recent(limit=10) == []
    mock_send_alert.assert_not_awaited()
    test_db.close()
