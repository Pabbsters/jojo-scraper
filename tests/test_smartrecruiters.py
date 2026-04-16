"""Tests for sources/smartrecruiters module."""

from __future__ import annotations

import pytest

from sources.smartrecruiters import (
    SMARTRECRUITERS_COMPANIES,
    is_intern_posting,
    parse_smartrecruiters_jobs,
)


# ── Mock data matching real SmartRecruiters API format ────────────────

MOCK_SR_RESPONSE: dict = {
    "offset": 0,
    "limit": 100,
    "totalFound": 3,
    "content": [
        {
            "id": "sr-001",
            "name": "Software Engineering Intern - Summer 2026",
            "releasedDate": "2026-03-01T10:00:00.000Z",
            "ref": "https://jobs.smartrecruiters.com/SnapInc/sr-001",
            "location": {
                "country": "us",
                "city": "Los Angeles",
                "remote": False,
            },
            "department": {"id": "d1", "label": "Engineering"},
        },
        {
            "id": "sr-002",
            "name": "Senior Staff Engineer",
            "releasedDate": "2026-03-02T10:00:00.000Z",
            "ref": "https://jobs.smartrecruiters.com/SnapInc/sr-002",
            "location": {"country": "us", "city": "Seattle", "remote": False},
            "department": {"id": "d1", "label": "Engineering"},
        },
        {
            "id": "sr-003",
            "name": "Data Science Internship",
            "releasedDate": "2026-03-03T10:00:00.000Z",
            "ref": "https://jobs.smartrecruiters.com/SnapInc/sr-003",
            "location": {"country": "us", "city": "", "remote": True},
            "department": {"id": "d2", "label": "Data"},
        },
    ],
}

MOCK_SR_EMPTY: dict = {"offset": 0, "limit": 100, "totalFound": 0, "content": []}


class TestIsInternPosting:
    """Test intern title pattern matching."""

    def test_matches_intern(self) -> None:
        assert is_intern_posting("Software Engineering Intern - Summer 2026") is True

    def test_matches_internship(self) -> None:
        assert is_intern_posting("Data Science Internship") is True

    def test_rejects_senior(self) -> None:
        assert is_intern_posting("Senior Staff Engineer") is False

    def test_rejects_manager(self) -> None:
        assert is_intern_posting("Engineering Manager") is False


class TestParseSmartrecruitersJobs:
    """Test parsing of SmartRecruiters API responses."""

    def test_filters_to_intern_only(self) -> None:
        results = parse_smartrecruiters_jobs("snap", "Snap", MOCK_SR_RESPONSE)
        titles = [r["title"] for r in results]
        assert "Software Engineering Intern - Summer 2026" in titles
        assert "Data Science Internship" in titles
        assert "Senior Staff Engineer" not in titles

    def test_correct_count(self) -> None:
        results = parse_smartrecruiters_jobs("snap", "Snap", MOCK_SR_RESPONSE)
        assert len(results) == 2

    def test_correct_field_mapping(self) -> None:
        results = parse_smartrecruiters_jobs("snap", "Snap", MOCK_SR_RESPONSE)
        intern = next(r for r in results if r["posting_id"] == "sr-001")
        assert intern["title"] == "Software Engineering Intern - Summer 2026"
        assert intern["url"] == "https://jobs.smartrecruiters.com/SnapInc/sr-001"
        assert intern["company_slug"] == "snap"
        assert intern["company_name"] == "Snap"
        assert intern["team"] == "Engineering"
        assert intern["location"] == "Los Angeles, US"

    def test_remote_location(self) -> None:
        results = parse_smartrecruiters_jobs("snap", "Snap", MOCK_SR_RESPONSE)
        ds = next(r for r in results if r["posting_id"] == "sr-003")
        assert ds["location"] == "Remote"

    def test_posted_at_date_only(self) -> None:
        results = parse_smartrecruiters_jobs("snap", "Snap", MOCK_SR_RESPONSE)
        intern = next(r for r in results if r["posting_id"] == "sr-001")
        assert intern["posted_at"] == "2026-03-01"

    def test_empty_content_returns_empty(self) -> None:
        results = parse_smartrecruiters_jobs("snap", "Snap", MOCK_SR_EMPTY)
        assert results == []

    def test_empty_dict_returns_empty(self) -> None:
        results = parse_smartrecruiters_jobs("snap", "Snap", {})
        assert results == []

    def test_posting_id_is_string(self) -> None:
        results = parse_smartrecruiters_jobs("snap", "Snap", MOCK_SR_RESPONSE)
        for r in results:
            assert isinstance(r["posting_id"], str)


class TestSmartrecruitersCompanies:
    """Validate the SMARTRECRUITERS_COMPANIES config."""

    def test_all_companies_have_required_keys(self) -> None:
        for company in SMARTRECRUITERS_COMPANIES:
            assert "slug" in company
            assert "company_id" in company
            assert "name" in company

    def test_expected_companies_present(self) -> None:
        slugs = {c["slug"] for c in SMARTRECRUITERS_COMPANIES}
        assert "snap" in slugs
        assert "spotify" in slugs
        assert "grammarly" in slugs
        assert "millennium" in slugs

    def test_slugs_are_unique(self) -> None:
        slugs = [c["slug"] for c in SMARTRECRUITERS_COMPANIES]
        assert len(slugs) == len(set(slugs))
