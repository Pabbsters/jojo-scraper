"""Live smoke check for every preferred direct company source."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import TIER1_COMPANIES, TIER1_SOURCE_PREFERENCES
from sources import (
    airbnb,
    amazon,
    apple,
    ashby,
    google,
    greenhouse,
    lever,
    netflix,
    official_pages,
    smartrecruiters,
    talentbrew,
    workday,
    workday_api,
)


GREENHOUSE_BY_SLUG = {company["slug"]: company for company in greenhouse.GREENHOUSE_COMPANIES}
ASHBY_BY_SLUG = {company["slug"]: company for company in ashby.ASHBY_COMPANIES}
LEVER_BY_SLUG = {company["slug"]: company for company in lever.LEVER_COMPANIES}
SMARTRECRUITERS_BY_SLUG = {
    company["slug"]: company for company in smartrecruiters.SMARTRECRUITERS_COMPANIES
}
WORKDAY_BY_SLUG = {company["slug"]: company for company in workday.WORKDAY_COMPANIES}
WORKDAY_API_BY_SLUG = {
    company["slug"]: company for company in workday_api.WORKDAY_API_COMPANIES
}
TALENTBREW_BY_SLUG = {
    company["slug"]: company for company in talentbrew.TALENTBREW_COMPANIES
}
OFFICIAL_PAGES_BY_SLUG = {
    company["slug"]: company for company in official_pages.OFFICIAL_PAGE_COMPANIES
}


async def _fetch_company_postings(company_slug: str) -> list[dict[str, Any]]:
    preferred = TIER1_SOURCE_PREFERENCES[company_slug]["preferred_source"]

    if preferred == "greenhouse":
        company = GREENHOUSE_BY_SLUG[company_slug]
        return await greenhouse.fetch_jobs(
            company["slug"],
            company["name"],
            board_slug=company.get("board_slug"),
        )
    if preferred == "ashby":
        company = ASHBY_BY_SLUG[company_slug]
        return await ashby.fetch_jobs(
            company["slug"],
            company["name"],
            board_slug=company.get("board_slug"),
        )
    if preferred == "lever":
        company = LEVER_BY_SLUG[company_slug]
        return await lever.fetch_jobs(
            company["slug"],
            company["name"],
            board_slug=company.get("board_slug"),
        )
    if preferred == "smartrecruiters":
        company = SMARTRECRUITERS_BY_SLUG[company_slug]
        return await smartrecruiters.fetch_jobs(
            company["slug"],
            company["company_id"],
            company["name"],
        )
    if preferred == "workday":
        company = WORKDAY_BY_SLUG[company_slug]
        return await workday.fetch_company_page(
            host=company["host"],
            path=company["path"],
            slug=company["slug"],
            name=company["name"],
        )
    if preferred == "workday_api":
        company = WORKDAY_API_BY_SLUG[company_slug]
        return await workday_api.fetch_jobs(
            slug=company["slug"],
            name=company["name"],
            host=company["host"],
            tenant=company["tenant"],
            site=company["site"],
        )
    if preferred == "talentbrew":
        company = TALENTBREW_BY_SLUG[company_slug]
        return await talentbrew.poll_company(
            company["slug"],
            company["name"],
            search_url=company["search_url"],
            base_url=company["base_url"],
        )
    if preferred == "official_pages":
        company = OFFICIAL_PAGES_BY_SLUG[company_slug]
        return await official_pages.fetch_jobs(company)
    if preferred == "google":
        return [posting for posting in await google.poll_all() if posting["company_slug"] == company_slug]
    if preferred == "amazon":
        return [posting for posting in await amazon.poll_all() if posting["company_slug"] == company_slug]
    if preferred == "apple":
        return [posting for posting in await apple.poll_all() if posting["company_slug"] == company_slug]
    if preferred == "airbnb":
        return [posting for posting in await airbnb.poll_all() if posting["company_slug"] == company_slug]
    if preferred == "netflix":
        return [posting for posting in await netflix.poll_all() if posting["company_slug"] == company_slug]

    raise ValueError(f"Unsupported preferred source: {preferred}")


async def _smoke_company(company: dict[str, str]) -> dict[str, Any]:
    slug = company["slug"]
    source = TIER1_SOURCE_PREFERENCES[slug]["preferred_source"]
    try:
        postings = await _fetch_company_postings(slug)
    except Exception as exc:
        return {
            "company_slug": slug,
            "preferred_source": source,
            "status": "error",
            "posting_count": 0,
            "detail": str(exc),
        }

    sample = postings[0]["title"] if postings else ""
    return {
        "company_slug": slug,
        "preferred_source": source,
        "status": "parseable_postings" if postings else "valid_zero_result",
        "posting_count": len(postings),
        "detail": sample,
    }


async def _main() -> int:
    results = []
    for company in TIER1_COMPANIES:
        results.append(await _smoke_company(company))

    for result in results:
        print(json.dumps(result, sort_keys=True))

    return 1 if any(result["status"] == "error" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
