"""Airbnb official positions scraper."""

from __future__ import annotations

import html
import json
import re
from typing import Any

import httpx

from config import ALERT_TITLE_PATTERNS

AIRBNB_SEARCH_URL = "https://careers.airbnb.com/positions/?search=intern"
AIRBNB_BASE_URL = "https://careers.airbnb.com"

_CARD_RE = re.compile(
    r"<li class=\"inner-grid.*?>.*?<div class=\"flex text-size-3.*?>\s*"
    r"<span>\s*(?P<team>.*?)\s*</span>.*?"
    r"<a href=\"(?P<url>https://careers\.airbnb\.com/positions/\d+/)\"[^>]*>\s*"
    r"(?P<title>.*?)\s*</a>.*?"
    r"flex items-center\">\s*(?P<location>.*?)\s*</span>",
    re.DOTALL,
)
_GRAPH_RE = re.compile(
    r"<script type=\"application/ld\+json\" class=\"yoast-schema-graph\">(?P<json>.*?)</script>",
    re.DOTALL,
)
_BODY_RE = re.compile(r"<div class=\"job-description.*?>(?P<body>.*?)</div>", re.DOTALL)


def is_intern_posting(title: str) -> bool:
    """Check if title matches any intern pattern."""
    title_lower = title.lower()
    return any(re.search(pattern, title_lower) for pattern in ALERT_TITLE_PATTERNS)


def parse_search_results(html_text: str) -> list[dict]:
    """Extract internship cards from Airbnb's rendered positions page."""
    results: list[dict] = []
    for match in _CARD_RE.finditer(html_text):
        title = html.unescape(match.group("title")).strip()
        if not is_intern_posting(title):
            continue
        url = html.unescape(match.group("url")).strip()
        posting_id = url.rstrip("/").split("/")[-1]
        results.append(
            {
                "posting_id": posting_id,
                "title": title,
                "url": url,
                "company_slug": "airbnb",
                "company_name": "Airbnb",
                "team": html.unescape(match.group("team")).strip(),
                "skills": "",
                "location": html.unescape(match.group("location")).strip(),
                "posted_at": "",
            }
        )
    return results


def enrich_detail(posting: dict, html_text: str) -> dict:
    """Fill in posted date and description from an Airbnb detail page."""
    enriched = dict(posting)
    graph_match = _GRAPH_RE.search(html_text)
    if graph_match:
        try:
            payload: dict[str, Any] = json.loads(graph_match.group("json"))
        except json.JSONDecodeError:
            payload = {}
        graph = payload.get("@graph", [])
        if isinstance(graph, list):
            webpage = next(
                (
                    item for item in graph
                    if isinstance(item, dict) and item.get("@type") == "WebPage"
                ),
                {},
            )
            enriched["posted_at"] = str(webpage.get("datePublished", "")).strip()

    body_match = _BODY_RE.search(html_text)
    if body_match:
        body = html.unescape(body_match.group("body"))
        enriched["skills"] = re.sub(r"<[^>]+>", " ", body).strip()[:200]
    return enriched


async def poll_all() -> list[dict]:
    """Fetch internship jobs from Airbnb's official positions site."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        search_response = await client.get(AIRBNB_SEARCH_URL)
        search_response.raise_for_status()
        candidates = parse_search_results(search_response.text)
        results: list[dict] = []
        for posting in candidates:
            detail_response = await client.get(posting["url"])
            detail_response.raise_for_status()
            results.append(enrich_detail(posting, detail_response.text))
        return results
