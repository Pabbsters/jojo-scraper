"""Tests for the Google careers source adapter."""

from __future__ import annotations

from sources.google import is_intern_posting, parse_google_jobs


MOCK_GOOGLE_HTML = """
<html><body>
<ul>
  <li class="lLd3Je">
    <h3 class="QJPWVe">Software Engineering Intern, Summer 2026</h3>
    <a href="jobs/results/116505799294886598-software-engineering-intern-summer-2026?employment_type=INTERN"></a>
    <span>Google</span>
    <span class="r0wTof ">Waterloo, ON, Canada</span>
    <span>Intern &amp; Apprentice</span>
  </li>
  <li class="lLd3Je">
    <h3 class="QJPWVe">Staff Software Engineer</h3>
    <a href="jobs/results/999999999-staff-software-engineer"></a>
    <span>Google</span>
    <span class="r0wTof ">Mountain View, CA, USA</span>
    <span>Intern &amp; Apprentice</span>
  </li>
</ul>
</body></html>
"""


def test_is_intern_posting_matches_intern_title() -> None:
    assert is_intern_posting("Software Engineering Intern") is True


def test_is_intern_posting_rejects_non_intern_title() -> None:
    assert is_intern_posting("Staff Software Engineer") is False


def test_parse_google_jobs_extracts_intern_cards() -> None:
    results = parse_google_jobs(MOCK_GOOGLE_HTML)
    assert len(results) == 1
    job = results[0]
    assert job["posting_id"] == "116505799294886598"
    assert job["title"] == "Software Engineering Intern, Summer 2026"
    assert job["url"].startswith("https://www.google.com/about/careers/applications/jobs/results/")
    assert job["company_slug"] == "google"
    assert job["company_name"] == "Google"
    assert job["location"] == "Waterloo, ON, Canada"
