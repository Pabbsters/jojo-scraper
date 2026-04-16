"""Tests for the TalentBrew direct-source adapter."""

from __future__ import annotations

from sources.talentbrew import enrich_detail, parse_search_results


SEARCH_HTML = """
<li>
  <a href="/job/mountain-view/summer-2026-mid-market-strategy-and-transformation-intern/27595/93999962928">
    <h2>Summer 2026 - Mid Market Strategy &amp; Transformation Intern</h2>
    <span class="job-location">Mountain View, California</span>
  </a>
</li>
<li>
  <a href="/job/mountain-view/staff-data-scientist/27595/93999962544">
    <h2>Staff Data Scientist</h2>
    <span class="job-location">Mountain View, California</span>
  </a>
</li>
"""

DETAIL_HTML = """
<script type="application/ld+json">
{
  "@context": "http://schema.org",
  "@type": "JobPosting",
  "datePosted": "2026-04-06",
  "description": "<p>Partner with strategy leaders and build analytics systems.</p>",
  "jobLocation": {
    "@type": "Place",
    "address": {"addressLocality": "Mountain View, California"}
  }
}
</script>
"""


def test_parse_search_results_filters_to_intern_roles() -> None:
    results = parse_search_results("intuit", "Intuit", SEARCH_HTML)
    assert len(results) == 1
    assert results[0]["title"] == "Summer 2026 - Mid Market Strategy & Transformation Intern"
    assert results[0]["location"] == "Mountain View, California"


def test_enrich_detail_threads_posted_date_and_description() -> None:
    posting = parse_search_results("intuit", "Intuit", SEARCH_HTML)[0]
    enriched = enrich_detail(posting, DETAIL_HTML, "https://jobs.intuit.com")
    assert enriched["url"].startswith("https://jobs.intuit.com/job/")
    assert enriched["posted_at"] == "2026-04-06"
    assert "analytics systems" in enriched["skills"]
