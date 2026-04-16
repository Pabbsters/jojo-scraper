"""TalentBrew careers scraper for direct company search pages."""

from __future__ import annotations

import html
import json
import re
from typing import Any

import httpx

from config import ALERT_TITLE_PATTERNS

TALENTBREW_COMPANIES: list[dict[str, str]] = [
    {
        "slug": "intuit",
        "name": "Intuit",
        "search_url": "https://jobs.intuit.com/search-jobs",
        "base_url": "https://jobs.intuit.com",
    },
]

_RESULT_RE = re.compile(
    r"<li[^>]*>\s*<a href=\"(?P<path>/job/[^\"]+)\"[^>]*>\s*"
    r"<h2>(?P<title>.*?)</h2>.*?"
    r"<span class=\"job-location\">(?P<location>.*?)</span>",
    re.DOTALL,
)
_DETAIL_JSONLD_RE = re.compile(
    r"<script type=\"application/ld\+json\">(?P<json>.*?)</script>",
    re.DOTALL,
)


def is_intern_posting(title: str) -> bool:
    """Check if title matches any intern pattern."""
    title_lower = title.lower()
    return any(re.search(pattern, title_lower) for pattern in ALERT_TITLE_PATTERNS)


def parse_search_results(company_slug: str, company_name: str, html_text: str) -> list[dict]:
    """Extract candidate TalentBrew postings from a rendered search page."""
    results: list[dict] = []
    for match in _RESULT_RE.finditer(html_text):
        title = html.unescape(match.group("title")).strip()
        if not is_intern_posting(title):
            continue
        path = html.unescape(match.group("path")).strip()
        posting_id = path.rstrip("/").split("/")[-1]
        results.append(
            {
                "posting_id": posting_id,
                "title": title,
                "url": path,
                "company_slug": company_slug,
                "company_name": company_name,
                "team": "",
                "skills": "",
                "location": html.unescape(match.group("location")).strip(),
                "posted_at": "",
            }
        )
    return results


def enrich_detail(posting: dict, html_text: str, base_url: str) -> dict:
    """Fill in description and posted date from a TalentBrew detail page."""
    enriched = dict(posting)
    match = _DETAIL_JSONLD_RE.search(html_text)
    if not match:
        if enriched["url"].startswith("/"):
            enriched["url"] = f"{base_url}{enriched['url']}"
        return enriched

    try:
        payload: dict[str, Any] = json.loads(match.group("json"))
    except json.JSONDecodeError:
        payload = {}

    if enriched["url"].startswith("/"):
        enriched["url"] = f"{base_url}{enriched['url']}"
    enriched["posted_at"] = str(payload.get("datePosted", "")).strip()
    description = html.unescape(str(payload.get("description", "") or "")).strip()
    enriched["skills"] = re.sub(r"<[^>]+>", " ", description).strip()[:200]
    location = payload.get("jobLocation", {})
    if isinstance(location, dict):
        address = location.get("address", {})
        if isinstance(address, dict):
            locality = address.get("addressLocality", "")
            if locality:
                enriched["location"] = locality
    return enriched


async def poll_company(
    company_slug: str,
    company_name: str,
    *,
    search_url: str,
    base_url: str,
) -> list[dict]:
    """Fetch a TalentBrew search page and hydrate matching internship jobs."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        search_response = await client.get(search_url)
        search_response.raise_for_status()
        candidates = parse_search_results(company_slug, company_name, search_response.text)
        results: list[dict] = []
        for posting in candidates:
            detail_response = await client.get(
                posting["url"] if posting["url"].startswith("http") else f"{base_url}{posting['url']}"
            )
            detail_response.raise_for_status()
            results.append(enrich_detail(posting, detail_response.text, base_url))
        return results


async def poll_all() -> list[dict]:
    """Fetch internship jobs from configured TalentBrew career sites."""
    results: list[dict] = []
    for company in TALENTBREW_COMPANIES:
        try:
            jobs = await poll_company(
                company["slug"],
                company["name"],
                search_url=company["search_url"],
                base_url=company["base_url"],
            )
            results.extend(jobs)
        except Exception:
            pass
    return results
