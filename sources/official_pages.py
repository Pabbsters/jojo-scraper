"""Official careers-page adapters for direct sources without clean ATS APIs."""

from __future__ import annotations

import html
import json
import re
from typing import Callable

import httpx

from config import ALERT_TITLE_PATTERNS

OFFICIAL_PAGE_COMPANIES: list[dict[str, str]] = [
    {
        "slug": "deshaw",
        "name": "D.E. Shaw",
        "url": "https://www.deshaw.com/careers",
    },
    {
        "slug": "sig",
        "name": "SIG",
        "url": "https://careers.sig.com/",
    },
    {
        "slug": "meta",
        "name": "Meta",
        "url": "https://www.metacareers.com/jobsearch/?q=intern",
    },
    {
        "slug": "microsoft",
        "name": "Microsoft",
        "url": "https://jobs.careers.microsoft.com/global/en/search?q=intern",
    },
    {
        "slug": "bytedance",
        "name": "ByteDance",
        "url": "https://jobs.bytedance.com/en/position?keywords=intern",
    },
]

_DESHAW_CARD_RE = re.compile(
    r'<div class="job" data-job-id="(?P<id>\d+)">.*?'
    r'<span class="location">(?P<location>.*?)</span>.*?'
    r'href="(?P<path>/careers/(?P<slug>[^"]+))".*?'
    r'<span class="job-display-name">(?P<title>.*?)</span>',
    re.DOTALL,
)
_SIG_LINK_RE = re.compile(
    r'href="(?P<path>https://careers\.sig\.com/us/en/job/(?P<id>[^"/]+)/[^"]+|/us/en/job/(?P<id2>[^"/]+)/[^"]+)"'
    r'[^>]*data-ph-at-job-title-text="(?P<title>[^"]+)"'
    r'[^>]*data-ph-at-job-location-text="(?P<location>[^"]*)"',
    re.DOTALL,
)
_META_JSON_RE = re.compile(
    r'"job_id":"(?P<id>\d+)".*?"title":"(?P<title>[^"]+)".*?"locations":\[(?P<locations>.*?)\]',
    re.DOTALL,
)
_META_LINK_RE = re.compile(
    r'<a[^>]+href="(?P<path>/jobs/(?P<id>\d+)/[^"]*)"[^>]*>(?P<title>.*?)</a>',
    re.DOTALL,
)
_MICROSOFT_JSON_RE = re.compile(
    r'"title":"(?P<title>[^"]+)".*?"display_job_id":"(?P<id>[^"]+)".*?'
    r'"canonicalPositionPath":"(?P<path>/[^"]+)".*?"posted_ts":"(?P<posted_at>[^"]*)".*?'
    r'"locations":\[(?P<locations>.*?)\]',
    re.DOTALL,
)
_BYTEDANCE_JSON_RE = re.compile(
    r'"recruitment_id":"?(?P<id>\d+)"?.*?"title":"(?P<title>[^"]+)".*?'
    r'"city_info":"(?P<location>[^"]*)".*?"publish_time":"(?P<posted_at>[^"]*)"',
    re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")


def is_intern_posting(title: str) -> bool:
    """Check if a title matches the alertable internship vocabulary."""
    title_lower = title.lower()
    return any(re.search(pattern, title_lower) for pattern in ALERT_TITLE_PATTERNS)


def _clean(value: str) -> str:
    return html.unescape(_TAG_RE.sub(" ", value)).strip()


def _extract_location_array(raw: str) -> str:
    matches = re.findall(r'"(?:name|title|display_name|label)":"([^"]+)"', raw)
    if matches:
        return ", ".join(dict.fromkeys(_clean(match) for match in matches if match.strip()))
    return ""


def parse_deshaw_jobs(html_text: str) -> list[dict]:
    """Parse D.E. Shaw's rendered careers cards."""
    results: list[dict] = []
    for match in _DESHAW_CARD_RE.finditer(html_text):
        title = _clean(match.group("title"))
        if not is_intern_posting(title):
            continue
        results.append(
            {
                "posting_id": match.group("id"),
                "title": title,
                "url": f"https://www.deshaw.com{match.group('path')}",
                "company_slug": "deshaw",
                "company_name": "D.E. Shaw",
                "team": "",
                "skills": "",
                "location": _clean(match.group("location")),
                "posted_at": "",
            }
        )
    return results


def parse_sig_jobs(html_text: str) -> list[dict]:
    """Parse SIG jobs from public Phenom-style job links when present."""
    results: list[dict] = []
    for match in _SIG_LINK_RE.finditer(html_text):
        title = _clean(match.group("title"))
        if not is_intern_posting(title):
            continue
        results.append(
            {
                "posting_id": match.group("id") or match.group("id2"),
                "title": title,
                "url": match.group("path")
                if match.group("path").startswith("http")
                else f"https://careers.sig.com{match.group('path')}",
                "company_slug": "sig",
                "company_name": "SIG",
                "team": "",
                "skills": "",
                "location": _clean(match.group("location")),
                "posted_at": "",
            }
        )
    return results


def parse_meta_jobs(html_text: str) -> list[dict]:
    """Parse Meta jobs from embedded JSON or public job links."""
    results: list[dict] = []
    seen_ids: set[str] = set()
    for match in _META_JSON_RE.finditer(html_text):
        title = _clean(match.group("title"))
        if not is_intern_posting(title):
            continue
        posting_id = match.group("id")
        seen_ids.add(posting_id)
        results.append(
            {
                "posting_id": posting_id,
                "title": title,
                "url": f"https://www.metacareers.com/jobs/{posting_id}/",
                "company_slug": "meta",
                "company_name": "Meta",
                "team": "",
                "skills": "",
                "location": _extract_location_array(match.group("locations")),
                "posted_at": "",
            }
        )
    for match in _META_LINK_RE.finditer(html_text):
        posting_id = match.group("id")
        if posting_id in seen_ids:
            continue
        title = _clean(match.group("title"))
        if not is_intern_posting(title):
            continue
        results.append(
            {
                "posting_id": posting_id,
                "title": title,
                "url": f"https://www.metacareers.com{match.group('path')}",
                "company_slug": "meta",
                "company_name": "Meta",
                "team": "",
                "skills": "",
                "location": "",
                "posted_at": "",
            }
        )
    return results


def parse_microsoft_jobs(html_text: str) -> list[dict]:
    """Parse Microsoft jobs from embedded position state when present."""
    results: list[dict] = []
    for match in _MICROSOFT_JSON_RE.finditer(html_text):
        title = _clean(match.group("title"))
        if not is_intern_posting(title):
            continue
        results.append(
            {
                "posting_id": match.group("id"),
                "title": title,
                "url": f"https://jobs.careers.microsoft.com{match.group('path')}",
                "company_slug": "microsoft",
                "company_name": "Microsoft",
                "team": "",
                "skills": "",
                "location": _extract_location_array(match.group("locations")),
                "posted_at": _clean(match.group("posted_at")),
            }
        )
    return results


def parse_bytedance_jobs(html_text: str) -> list[dict]:
    """Parse ByteDance jobs from embedded search state when present."""
    results: list[dict] = []
    for match in _BYTEDANCE_JSON_RE.finditer(html_text):
        title = _clean(match.group("title"))
        if not is_intern_posting(title):
            continue
        posting_id = match.group("id")
        results.append(
            {
                "posting_id": posting_id,
                "title": title,
                "url": f"https://jobs.bytedance.com/en/position/{posting_id}/detail",
                "company_slug": "bytedance",
                "company_name": "ByteDance",
                "team": "",
                "skills": "",
                "location": _clean(match.group("location")),
                "posted_at": _clean(match.group("posted_at")),
            }
        )
    return results


_PARSERS: dict[str, Callable[[str], list[dict]]] = {
    "deshaw": parse_deshaw_jobs,
    "sig": parse_sig_jobs,
    "meta": parse_meta_jobs,
    "microsoft": parse_microsoft_jobs,
    "bytedance": parse_bytedance_jobs,
}


async def fetch_jobs(company: dict[str, str]) -> list[dict]:
    """Fetch one official careers page and parse any public internship data."""
    parser = _PARSERS[company["slug"]]
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(company["url"])
        response.raise_for_status()
        return parser(response.text)


async def poll_all() -> list[dict]:
    """Poll all supported official careers pages and return normalized jobs."""
    results: list[dict] = []
    for company in OFFICIAL_PAGE_COMPANIES:
        try:
            results.extend(await fetch_jobs(company))
        except Exception:
            pass
    return results
