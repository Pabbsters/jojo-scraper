"""Main entry point for jojo-scraper: scheduler + feed server."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import POLL_INTERVAL_MINUTES, TIER1_COMPANIES, TIER1_SOURCE_PREFERENCES
from db import PostingDB, _canonical_identity_for_posting
from discord_alert import send_alert
from feed import start_feed_server
from matching import classify_posting
from sources import (
    amazon,
    apple,
    ashby,
    google,
    greenhouse,
    lever,
    workday,
)
from targeting import should_accept_posting

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("jojo")

db = PostingDB(os.environ.get("DB_PATH", "postings.db"))
_TIER1_COMPANY_SLUGS = {company["slug"] for company in TIER1_COMPANIES}


def _get_tier1_source_preference(company_slug: str) -> dict[str, str] | None:
    """Return the preferred source config for a tier-1 company, if any."""
    return TIER1_SOURCE_PREFERENCES.get(company_slug)


def _get_company_tier(company_slug: str) -> str:
    """Return the tier label for a company slug."""
    return "tier_1" if company_slug in _TIER1_COMPANY_SLUGS else ""


async def process_postings(
    postings: list[dict],
    source: str,
    *,
    now: datetime | None = None,
) -> None:
    """Check each posting against DB, classify, store, and alert."""
    new_count = 0
    reference_time = now or datetime.now(UTC)
    for p in postings:
        posting = dict(p)
        posting_id = str(p.get("posting_id", ""))
        company_slug = str(p.get("company_slug", "unknown")).strip()
        preferred_source = _get_tier1_source_preference(company_slug)
        tier = _get_company_tier(company_slug)

        if not should_accept_posting(posting, source, now=reference_time):
            continue

        canonical_source, canonical_posting_id = _canonical_identity_for_posting(
            source,
            company_slug,
            posting_id,
            str(p.get("url", "")),
        )
        if not canonical_posting_id:
            continue

        canonical_is_new = db.is_new(canonical_source, company_slug, canonical_posting_id)

        match = classify_posting(p.get("title", ""), p.get("description", ""))
        if match is None:
            continue

        posting["track"] = match["track"]
        posting["tier"] = tier
        posting["matched_keyword"] = match.get("matched_keyword", "")
        posting["key_skills"] = str(
            posting.get("key_skills") or posting.get("skills", "")
        ).strip()
        if p.get("posted_at"):
            posting["posted_at"] = str(p.get("posted_at"))
        posting["source_type"] = (
            "direct" if preferred_source is not None and source == canonical_source else ""
        )
        posting["canonical_source"] = canonical_source
        posting["canonical_posting_id"] = canonical_posting_id
        db.mark_seen(
            source=source,
            company_slug=company_slug,
            posting_id=posting_id,
            title=posting.get("title", ""),
            url=posting.get("url", ""),
            track=match["track"],
            company_name=posting.get("company_name", ""),
            skills=posting.get("skills", ""),
            comp=posting.get("comp", ""),
            team=posting.get("team", ""),
            deadline=posting.get("deadline", ""),
            tier=tier,
            source_type=posting["source_type"],
            matched_keyword=posting["matched_keyword"],
            key_skills=posting["key_skills"],
            posted_at=posting.get("posted_at", ""),
            canonical_source=canonical_source,
            canonical_posting_id=canonical_posting_id,
        )

        if canonical_is_new:
            stored_row = db.get_recent(limit=1)[0]
            posting["first_seen_at"] = stored_row.get("first_seen_at", 0)
            try:
                await send_alert(posting)
            except Exception as e:
                logger.error("Failed to send alert: %s", e)

            new_count += 1

    if new_count > 0:
        logger.info("[%s] %d new postings found and alerted", source, new_count)


# ── Poll functions for each source ────────────────────────────────────


async def poll_greenhouse() -> None:
    postings = await greenhouse.poll_all()
    await process_postings(postings, "greenhouse")


async def poll_ashby() -> None:
    postings = await ashby.poll_all()
    await process_postings(postings, "ashby")


async def poll_lever() -> None:
    postings = await lever.poll_all()
    await process_postings(postings, "lever")


async def poll_amazon_jobs() -> None:
    postings = await amazon.poll_all()
    await process_postings(postings, "amazon")


async def poll_google_jobs() -> None:
    postings = await google.poll_all()
    await process_postings(postings, "google")


async def poll_apple_jobs() -> None:
    postings = await apple.poll_all()
    await process_postings(postings, "apple")


async def poll_workday_feeds() -> None:
    postings = await workday.poll_all()
    await process_postings(postings, "workday")


async def _async_main() -> None:
    logger.info("Starting jojo-scraper")

    start_feed_server(db)
    logger.info("Feed server started on port 8080")

    scheduler = AsyncIOScheduler()

    # Tier 1: Direct APIs - every 15 min
    scheduler.add_job(
        poll_greenhouse,
        "interval",
        minutes=POLL_INTERVAL_MINUTES["greenhouse"],
        id="greenhouse",
        next_run_time=None,
    )
    scheduler.add_job(
        poll_ashby,
        "interval",
        minutes=POLL_INTERVAL_MINUTES["ashby"],
        id="ashby",
        next_run_time=None,
    )
    scheduler.add_job(
        poll_lever,
        "interval",
        minutes=POLL_INTERVAL_MINUTES["lever"],
        id="lever",
        next_run_time=None,
    )
    scheduler.add_job(
        poll_google_jobs,
        "interval",
        minutes=POLL_INTERVAL_MINUTES["google"],
        id="google",
        next_run_time=None,
    )
    scheduler.add_job(
        poll_amazon_jobs,
        "interval",
        minutes=POLL_INTERVAL_MINUTES["amazon"],
        id="amazon",
        next_run_time=None,
    )
    scheduler.add_job(
        poll_apple_jobs,
        "interval",
        minutes=POLL_INTERVAL_MINUTES["apple"],
        id="apple",
        next_run_time=None,
    )
    scheduler.add_job(
        poll_workday_feeds,
        "interval",
        minutes=POLL_INTERVAL_MINUTES["workday"],
        id="workday",
        next_run_time=None,
    )

    scheduler.start()
    logger.info("Scheduler started -- direct careers sources armed")

    # Run initial poll — individual failures are logged, not raised
    results = await asyncio.gather(
        poll_greenhouse(), poll_ashby(), poll_lever(),
        poll_google_jobs(), poll_amazon_jobs(), poll_apple_jobs(), poll_workday_feeds(),
        return_exceptions=True,
    )
    for r in results:
        if isinstance(r, Exception):
            logger.error("Initial poll error: %s", r)
    logger.info("Initial poll complete")

    # Keep running until interrupted
    await asyncio.Event().wait()


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
