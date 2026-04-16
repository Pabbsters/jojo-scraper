"""Targeting policy helpers for Jojo's direct-careers alert strategy."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import re
from typing import Any

from config import (
    ALLOWED_EMPLOYMENT_PATTERNS,
    DIRECT_ALERT_SOURCES,
    MAX_POST_AGE_HOURS,
    REMOTE_PATTERNS,
    SEASON_LOCATION_RULES,
    SEASON_PATTERNS,
    TIER1_SOURCE_PREFERENCES,
    TARGET_COMPANY_SLUGS,
    US_PATTERNS,
)


def _matches_any(patterns: list[str] | set[str], text: str) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _parse_datetime(value: object) -> datetime | None:
    if value in (None, ""):
        return None

    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)

    if isinstance(value, (int, float)):
        seconds = float(value)
        if seconds > 10_000_000_000:
            seconds /= 1000
        return datetime.fromtimestamp(seconds, tz=UTC)

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        if raw.isdigit():
            numeric = float(raw)
            if numeric > 10_000_000_000:
                numeric /= 1000
            return datetime.fromtimestamp(numeric, tz=UTC)
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None
        return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)

    return None


def _posting_text(posting: dict[str, Any]) -> str:
    parts = [
        str(posting.get("title", "")),
        str(posting.get("description", "")),
        str(posting.get("skills", "")),
        str(posting.get("team", "")),
        str(posting.get("location", "")),
    ]
    return " ".join(parts).lower()


def _detect_season(text: str) -> str | None:
    for season, patterns in SEASON_PATTERNS.items():
        if _matches_any(patterns, text):
            return season
    return None


def _is_fresh(posted_at: object, now: datetime) -> bool:
    parsed = _parse_datetime(posted_at)
    if parsed is None:
        return False
    age = now - parsed
    return timedelta(0) <= age <= timedelta(hours=MAX_POST_AGE_HOURS)


def _is_remote(text: str) -> bool:
    return _matches_any(REMOTE_PATTERNS, text)


def _is_us(text: str) -> bool:
    return _matches_any(US_PATTERNS, text)


def _has_allowed_employment_type(text: str) -> bool:
    return _matches_any(ALLOWED_EMPLOYMENT_PATTERNS, text)


def _preferred_source(company_slug: str) -> str | None:
    preferred = TIER1_SOURCE_PREFERENCES.get(company_slug)
    if preferred is None:
        return None
    return str(preferred.get("preferred_source", "")).strip().lower() or None


def should_accept_posting(
    posting: dict[str, Any],
    source: str,
    *,
    now: datetime | None = None,
) -> bool:
    """Return True when a posting satisfies the active alerting policy."""
    normalized_source = source.strip().lower()
    if normalized_source not in DIRECT_ALERT_SOURCES:
        return False

    company_slug = str(posting.get("company_slug", "")).strip().lower()
    if company_slug not in TARGET_COMPANY_SLUGS:
        return False

    preferred_source = _preferred_source(company_slug)
    if preferred_source is None or preferred_source != normalized_source:
        return False

    combined_text = _posting_text(posting)
    if not _has_allowed_employment_type(combined_text):
        return False

    season = _detect_season(combined_text)
    if season is None:
        return False

    location_rule = SEASON_LOCATION_RULES[season]
    if location_rule == "remote" and not _is_remote(combined_text):
        return False
    if location_rule == "us" and not _is_us(combined_text):
        return False

    reference = now or datetime.now(UTC)
    if not _is_fresh(posting.get("posted_at"), reference):
        return False

    posting["season"] = season
    return True
