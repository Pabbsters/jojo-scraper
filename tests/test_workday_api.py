"""Tests for sources/workday_api module."""

from __future__ import annotations

import pytest

from sources.workday_api import (
    WORKDAY_API_COMPANIES,
    _extract_csrf,
    fetch_jobs,
    is_intern_posting,
    parse_workday_api_jobs,
)


# ── Mock data matching Workday CXS API format ─────────────────────────

MOCK_WD_RESPONSE: dict = {
    "jobPostings": [
        {
            "title": "Software Engineering Intern - Summer 2026",
            "externalPath": "/job/Tesla-Software-Engineering-Intern-Summer-2026/12345",
            "postedOn": "2026-03-01",
            "locationsText": "Palo Alto, CA",
            "bulletFields": ["WD-12345"],
        },
        {
            "title": "Senior Staff Engineer",
            "externalPath": "/job/Tesla-Senior-Staff-Engineer/12346",
            "postedOn": "2026-03-02",
            "locationsText": "Austin, TX",
            "bulletFields": ["WD-12346"],
        },
        {
            "title": "Autopilot ML Internship",
            "externalPath": "/job/Tesla-Autopilot-ML-Internship/12347",
            "postedOn": "2026-03-03",
            "locationsText": "Fremont, CA",
            "bulletFields": ["WD-12347"],
        },
    ],
    "total": 3,
}

MOCK_WD_EMPTY: dict = {"jobPostings": [], "total": 0}


class TestIsInternPosting:
    def test_matches_intern(self) -> None:
        assert is_intern_posting("Software Engineering Intern - Summer 2026") is True

    def test_matches_internship(self) -> None:
        assert is_intern_posting("Autopilot ML Internship") is True

    def test_rejects_senior(self) -> None:
        assert is_intern_posting("Senior Staff Engineer") is False


class TestExtractCsrf:
    def test_extracts_from_set_cookie(self) -> None:
        import httpx
        headers = httpx.Headers({"set-cookie": "PLAY_SESSION=abc123; Path=/"})
        csrf = _extract_csrf(headers, "")
        assert csrf == "abc123"

    def test_extracts_from_html_fallback(self) -> None:
        import httpx
        headers = httpx.Headers({})
        html = 'window.__CONFIG__ = {"csrfToken": "token456"}'
        csrf = _extract_csrf(headers, html)
        assert csrf == "token456"

    def test_returns_none_when_missing(self) -> None:
        import httpx
        headers = httpx.Headers({})
        assert _extract_csrf(headers, "<html></html>") is None


class TestParseWorkdayApiJobs:
    def test_filters_to_intern_only(self) -> None:
        results = parse_workday_api_jobs("tesla", "Tesla", "tesla.wd1.myworkdayjobs.com", MOCK_WD_RESPONSE)
        titles = [r["title"] for r in results]
        assert "Software Engineering Intern - Summer 2026" in titles
        assert "Autopilot ML Internship" in titles
        assert "Senior Staff Engineer" not in titles

    def test_correct_count(self) -> None:
        results = parse_workday_api_jobs("tesla", "Tesla", "tesla.wd1.myworkdayjobs.com", MOCK_WD_RESPONSE)
        assert len(results) == 2

    def test_url_constructed_from_host_and_path(self) -> None:
        results = parse_workday_api_jobs("tesla", "Tesla", "tesla.wd1.myworkdayjobs.com", MOCK_WD_RESPONSE)
        intern = next(r for r in results if "Intern" in r["title"])
        assert intern["url"].startswith("https://tesla.wd1.myworkdayjobs.com")
        assert "12345" in intern["url"]

    def test_location_extracted(self) -> None:
        results = parse_workday_api_jobs("tesla", "Tesla", "tesla.wd1.myworkdayjobs.com", MOCK_WD_RESPONSE)
        intern = next(r for r in results if "Intern" in r["title"])
        assert intern["location"] == "Palo Alto, CA"

    def test_posted_at_iso_preserved(self) -> None:
        results = parse_workday_api_jobs("tesla", "Tesla", "tesla.wd1.myworkdayjobs.com", MOCK_WD_RESPONSE)
        intern = next(r for r in results if "Intern" in r["title"])
        assert intern["posted_at"] == "2026-03-01"

    def test_empty_response(self) -> None:
        results = parse_workday_api_jobs("tesla", "Tesla", "tesla.wd1.myworkdayjobs.com", MOCK_WD_EMPTY)
        assert results == []

    def test_company_slug_and_name(self) -> None:
        results = parse_workday_api_jobs("tesla", "Tesla", "tesla.wd1.myworkdayjobs.com", MOCK_WD_RESPONSE)
        for r in results:
            assert r["company_slug"] == "tesla"
            assert r["company_name"] == "Tesla"


class TestWorkdayApiCompanies:
    def test_all_companies_have_required_keys(self) -> None:
        for company in WORKDAY_API_COMPANIES:
            assert "slug" in company
            assert "name" in company
            assert "host" in company
            assert "tenant" in company
            assert "site" in company

    def test_tesla_present(self) -> None:
        slugs = {c["slug"] for c in WORKDAY_API_COMPANIES}
        assert "tesla" in slugs


@pytest.mark.asyncio
async def test_fetch_jobs_returns_empty_on_maintenance_page(monkeypatch) -> None:
    import httpx

    class MockResponse:
        def __init__(self, *, text: str = "", headers: httpx.Headers | None = None, status_code: int = 200):
            self.text = text
            self.headers = headers or httpx.Headers({})
            self.status_code = status_code

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise httpx.HTTPStatusError(
                    f"status {self.status_code}",
                    request=httpx.Request("GET", "https://example.com"),
                    response=httpx.Response(self.status_code, request=httpx.Request("GET", "https://example.com")),
                )

        def json(self) -> dict:
            return {}

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):
            return MockResponse(
                text='window.location.href = "https://community.workday.com/maintenance-page"',
            )

        async def post(self, url, json=None, headers=None):
            raise AssertionError("POST should not run when the careers page is in maintenance mode")

    monkeypatch.setattr(httpx, "AsyncClient", lambda *args, **kwargs: MockClient())
    jobs = await fetch_jobs("tesla", "Tesla", "tesla.wd1.myworkdayjobs.com", "tesla", "teslamotors")
    assert jobs == []
