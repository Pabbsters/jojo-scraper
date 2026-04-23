"""Tests for sources/official_pages module."""

from __future__ import annotations

from sources.official_pages import (
    OFFICIAL_PAGE_COMPANIES,
    parse_bytedance_jobs,
    parse_deshaw_jobs,
    parse_meta_jobs,
    parse_microsoft_jobs,
    parse_sig_jobs,
)


def test_parse_deshaw_jobs_extracts_visible_cards() -> None:
    html = """
    <div class="job" data-job-id="5852">
      <span class="location">New York</span>
      <a href="/careers/DESCOvery-Associate-5852">
        <span class="job-display-name">DESCOvery Associate Intern - Winter 2026</span>
      </a>
    </div>
    """
    results = parse_deshaw_jobs(html)
    assert len(results) == 1
    assert results[0]["posting_id"] == "5852"
    assert results[0]["company_slug"] == "deshaw"
    assert results[0]["url"] == "https://www.deshaw.com/careers/DESCOvery-Associate-5852"


def test_parse_sig_jobs_extracts_phenom_link_cards() -> None:
    html = """
    <a href="/us/en/job/9876/Quantitative-Research-Intern"
       data-ph-at-job-title-text="Quantitative Research Intern - Summer 2027"
       data-ph-at-job-location-text="Philadelphia, PA">
    </a>
    """
    results = parse_sig_jobs(html)
    assert len(results) == 1
    assert results[0]["posting_id"] == "9876"
    assert results[0]["location"] == "Philadelphia, PA"


def test_parse_meta_jobs_extracts_embedded_json() -> None:
    html = """
    {"job_id":"123456789","title":"AI Research Intern - Fall 2026",
     "locations":[{"name":"Remote - United States"}]}
    """
    results = parse_meta_jobs(html)
    assert len(results) == 1
    assert results[0]["posting_id"] == "123456789"
    assert results[0]["location"] == "Remote - United States"


def test_parse_microsoft_jobs_extracts_embedded_position_state() -> None:
    html = """
    {"title":"Software Engineering Intern - Winter 2026",
     "display_job_id":"1748383",
     "canonicalPositionPath":"/global/en/job/1748383/Software-Engineering-Intern",
     "posted_ts":"2026-04-20T00:00:00Z",
     "locations":[{"name":"Redmond, Washington, United States"}]}
    """
    results = parse_microsoft_jobs(html)
    assert len(results) == 1
    assert results[0]["posting_id"] == "1748383"
    assert results[0]["url"].endswith("/global/en/job/1748383/Software-Engineering-Intern")


def test_parse_bytedance_jobs_extracts_embedded_search_state() -> None:
    html = """
    {"recruitment_id":"5555","title":"Machine Learning Intern - Spring 2026",
     "city_info":"San Jose, CA","publish_time":"2026-04-21T00:00:00Z"}
    """
    results = parse_bytedance_jobs(html)
    assert len(results) == 1
    assert results[0]["posting_id"] == "5555"
    assert results[0]["location"] == "San Jose, CA"


def test_official_page_companies_cover_expected_slugs() -> None:
    slugs = {company["slug"] for company in OFFICIAL_PAGE_COMPANIES}
    assert slugs == {"deshaw", "sig", "meta", "microsoft", "bytedance"}
