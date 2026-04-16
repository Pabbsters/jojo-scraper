"""Lever API poller for intern job postings."""

from __future__ import annotations

import re
from datetime import UTC, datetime

import httpx

from config import ALERT_TITLE_PATTERNS, LEVER_COMPANIES

LEVER_API = "https://api.lever.co/v0/postings/{slug}?mode=json"


def is_intern_posting(title: str) -> bool:
    """Check if title matches any intern pattern."""
    title_lower = title.lower()
    return any(re.search(p, title_lower) for p in ALERT_TITLE_PATTERNS)


def _format_timestamp(raw: object) -> str:
    if raw in (None, ""):
        return ""
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return str(raw).strip()
    if value > 10_000_000_000:
        value /= 1000
    return datetime.fromtimestamp(value, tz=UTC).isoformat().replace("+00:00", "Z")


def parse_lever_jobs(
    company_slug: str, company_name: str, raw: list
) -> list[dict]:
    """Parse Lever API response into normalized posting dicts.

    Lever returns a JSON array of posting objects.
    Only includes postings where the title matches intern patterns.
    """
    results: list[dict] = []

    for job in raw:
        title = job.get("text", "")
        if not is_intern_posting(title):
            continue

        categories = job.get("categories", {})
        team = categories.get("team", "") or categories.get("department", "")

        description = job.get("descriptionPlain", "")
        skills = description[:200].strip() if description else ""

        location = categories.get("location", "")
        posted_at = _format_timestamp(job.get("createdAt") or job.get("updatedAt"))

        results.append({
            "posting_id": str(job.get("id", "")),
            "title": title,
            "url": job.get("hostedUrl", ""),
            "company_slug": company_slug,
            "company_name": company_name,
            "team": team,
            "skills": skills,
            "location": location,
            "posted_at": posted_at,
        })

    return results


async def fetch_jobs(
    company_slug: str,
    name: str,
    *,
    board_slug: str | None = None,
) -> list[dict]:
    """Fetch and parse jobs from Lever for one company."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(LEVER_API.format(slug=board_slug or company_slug))
        resp.raise_for_status()
        return parse_lever_jobs(company_slug, name, resp.json())


async def poll_all() -> list[dict]:
    """Fetch from all Lever companies. Return combined list."""
    results: list[dict] = []
    for company in LEVER_COMPANIES:
        try:
            jobs = await fetch_jobs(
                company["slug"],
                company["name"],
                board_slug=company.get("board_slug"),
            )
            results.extend(jobs)
        except Exception:
            pass  # Log in production, skip failed companies
    return results
