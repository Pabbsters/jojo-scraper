"""Tests for sources/netflix module."""

from __future__ import annotations

import pytest

from sources.netflix import is_intern_posting, parse_netflix_jobs


# ── Mock data matching Netflix jobs API format ────────────────────────

MOCK_NETFLIX_RESPONSE: dict = {
    "positions": [
        {
            "id": "JR123",
            "text": "Software Engineering Intern - Summer 2026",
            "location": {"name": "Los Gatos, CA"},
            "team": {"name": "Core Platform"},
            "externalUrl": "https://jobs.netflix.com/jobs/JR123",
            "created": 1740000000000,
        },
        {
            "id": "JR124",
            "text": "Staff Backend Engineer",
            "location": {"name": "Los Gatos, CA"},
            "team": {"name": "Streaming"},
            "externalUrl": "https://jobs.netflix.com/jobs/JR124",
            "created": 1740000000000,
        },
        {
            "id": "JR125",
            "text": "ML Research Internship",
            "location": "Remote",
            "team": "Data Science",
            "externalUrl": "https://jobs.netflix.com/jobs/JR125",
            "created": 1740100000000,
        },
    ],
    "count": 3,
}

MOCK_NETFLIX_JOBS_KEY: dict = {
    "jobs": [
        {
            "id": "JR200",
            "text": "Data Engineering Intern",
            "location": {"name": "New York, NY"},
            "team": {"name": "Data"},
            "externalUrl": "https://jobs.netflix.com/jobs/JR200",
            "created": 1740000000000,
        }
    ]
}

MOCK_NETFLIX_EMPTY: dict = {"positions": [], "count": 0}


class TestIsInternPosting:
    """Test intern title pattern matching."""

    def test_matches_intern(self) -> None:
        assert is_intern_posting("Software Engineering Intern - Summer 2026") is True

    def test_matches_internship(self) -> None:
        assert is_intern_posting("ML Research Internship") is True

    def test_rejects_staff(self) -> None:
        assert is_intern_posting("Staff Backend Engineer") is False


class TestParseNetflixJobs:
    """Test parsing of Netflix API responses."""

    def test_filters_to_intern_only(self) -> None:
        results = parse_netflix_jobs(MOCK_NETFLIX_RESPONSE)
        titles = [r["title"] for r in results]
        assert "Software Engineering Intern - Summer 2026" in titles
        assert "ML Research Internship" in titles
        assert "Staff Backend Engineer" not in titles

    def test_correct_count(self) -> None:
        results = parse_netflix_jobs(MOCK_NETFLIX_RESPONSE)
        assert len(results) == 2

    def test_correct_field_mapping(self) -> None:
        results = parse_netflix_jobs(MOCK_NETFLIX_RESPONSE)
        intern = next(r for r in results if r["posting_id"] == "JR123")
        assert intern["title"] == "Software Engineering Intern - Summer 2026"
        assert intern["url"] == "https://jobs.netflix.com/jobs/JR123"
        assert intern["company_slug"] == "netflix"
        assert intern["company_name"] == "Netflix"
        assert intern["team"] == "Core Platform"
        assert intern["location"] == "Los Gatos, CA"

    def test_string_location(self) -> None:
        results = parse_netflix_jobs(MOCK_NETFLIX_RESPONSE)
        ml = next(r for r in results if r["posting_id"] == "JR125")
        assert ml["location"] == "Remote"

    def test_string_team(self) -> None:
        results = parse_netflix_jobs(MOCK_NETFLIX_RESPONSE)
        ml = next(r for r in results if r["posting_id"] == "JR125")
        assert ml["team"] == "Data Science"

    def test_jobs_key_fallback(self) -> None:
        results = parse_netflix_jobs(MOCK_NETFLIX_JOBS_KEY)
        assert len(results) == 1
        assert results[0]["posting_id"] == "JR200"

    def test_empty_response(self) -> None:
        results = parse_netflix_jobs(MOCK_NETFLIX_EMPTY)
        assert results == []

    def test_empty_dict(self) -> None:
        results = parse_netflix_jobs({})
        assert results == []

    def test_posting_id_is_string(self) -> None:
        results = parse_netflix_jobs(MOCK_NETFLIX_RESPONSE)
        for r in results:
            assert isinstance(r["posting_id"], str)

    def test_timestamp_conversion(self) -> None:
        results = parse_netflix_jobs(MOCK_NETFLIX_RESPONSE)
        intern = next(r for r in results if r["posting_id"] == "JR123")
        assert "2025" in intern["posted_at"] or "2026" in intern["posted_at"]
        assert "T" in intern["posted_at"]

    def test_all_postings_have_company_slug(self) -> None:
        results = parse_netflix_jobs(MOCK_NETFLIX_RESPONSE)
        for r in results:
            assert r["company_slug"] == "netflix"
