"""Google Careers public-results poller for internship postings."""

from __future__ import annotations

import html
import re

import httpx

from config import ALERT_TITLE_PATTERNS

GOOGLE_JOBS_URL = "https://www.google.com/about/careers/applications/jobs/results/?employment_type=INTERN"

_CARD_RE = re.compile(
    r'<li class="lLd3Je".*?<h3 class="QJPWVe">(?P<title>[^<]+)</h3>.*?'
    r'href="(?P<href>jobs/results/[^"]+)".*?'
    r'<span>Google</span>.*?'
    r'<span class="r0wTof ">(?P<location>[^<]+)</span>.*?'
    r'<span>Intern &amp; Apprentice</span>',
    re.DOTALL,
)


def is_intern_posting(title: str) -> bool:
    """Check if title matches any alertable title pattern."""
    title_lower = title.lower()
    return any(re.search(pattern, title_lower) for pattern in ALERT_TITLE_PATTERNS)


def parse_google_jobs(raw_html: str) -> list[dict]:
    """Parse internship job cards from Google's public careers results page."""
    results: list[dict] = []

    for match in _CARD_RE.finditer(raw_html):
        title = html.unescape(match.group("title")).strip()
        if not is_intern_posting(title):
            continue

        relative_url = html.unescape(match.group("href")).strip()
        posting_id = relative_url.split("/", 2)[2].split("-", 1)[0]
        location = html.unescape(match.group("location")).strip()

        results.append(
            {
                "posting_id": posting_id,
                "title": title,
                "url": f"https://www.google.com/about/careers/applications/{relative_url}",
                "company_slug": "google",
                "company_name": "Google",
                "team": "",
                "skills": "",
                "location": location,
                "posted_at": "",
            }
        )

    return results


async def poll_all() -> list[dict]:
    """Fetch Google's public internship results page and parse job cards."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(GOOGLE_JOBS_URL)
        response.raise_for_status()
        return parse_google_jobs(response.text)
