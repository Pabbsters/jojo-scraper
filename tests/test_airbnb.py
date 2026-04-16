"""Tests for the Airbnb direct-source adapter."""

from __future__ import annotations

from sources.airbnb import enrich_detail, parse_search_results


SEARCH_HTML = """
<li class="inner-grid border-b border-gray-Foggy py-4" role="listitem">
  <div class="col-span-4 lg:col-span-9">
    <div class="flex text-size-3 font-medium text-gray-48 gap-1 mb-[5px]">
      <span>Early Career Program: Intern</span>
      <span>&#x2022;</span>
      <span>Live and Work Anywhere</span>
    </div>
    <span class="text-size-4">
      <a href="https://careers.airbnb.com/positions/7707299/" tabindex="0">
        Accounting Intern, Statutory Reporting
      </a>
    </span>
  </div>
  <div class="col-span-4 lg:col-span-3 flex justify-end text-right flex-wrap gap-1">
    <span class="text-size-4 font-normal text-gray-48 flex items-center">United States</span>
  </div>
</li>
"""

DETAIL_HTML = """
<script type="application/ld+json" class="yoast-schema-graph">
{
  "@context": "https://schema.org",
  "@graph": [
    {"@type": "WebPage", "datePublished": "2026-04-16T14:53:42+00:00"}
  ]
}
</script>
<div class="job-description rich-text"><p>Airbnb is seeking an Accounting Intern to join the Statutory Reporting team.</p></div>
"""


def test_parse_search_results_extracts_airbnb_cards() -> None:
    results = parse_search_results(SEARCH_HTML)
    assert len(results) == 1
    assert results[0]["company_slug"] == "airbnb"
    assert results[0]["team"] == "Early Career Program: Intern"
    assert results[0]["location"] == "United States"


def test_enrich_detail_extracts_published_date_and_description() -> None:
    posting = parse_search_results(SEARCH_HTML)[0]
    enriched = enrich_detail(posting, DETAIL_HTML)
    assert enriched["posted_at"] == "2026-04-16T14:53:42+00:00"
    assert "Accounting Intern" in enriched["skills"]
