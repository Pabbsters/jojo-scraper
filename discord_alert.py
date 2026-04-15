"""Discord webhook alert formatter and sender."""

from __future__ import annotations

from datetime import UTC, datetime
import os
import re
from zoneinfo import ZoneInfo

import httpx

from config import TRACK_EMOJI

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
CENTRAL_TZ = ZoneInfo("America/Chicago")

SOURCE_LABELS: dict[str, str] = {
    "greenhouse": "Greenhouse",
    "ashby": "Ashby",
    "lever": "Lever",
    "workday": "Workday",
    "amazon": "Amazon",
    "apple": "Apple",
    "jobspy": "JobSpy",
    "github": "GitHub",
    "reddit": "Reddit",
    "hn": "HN",
}

TRACK_PREFIXES: dict[str, str] = {
    "ai_data": "AI/DATA",
    "swe": "SWE",
    "sales_technical": "SALES/TECH",
    "consulting": "CONSULTING",
    "extras": "EXTRAS",
    "cloud_infra": "CLOUD/INFRA",
}


def _utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(UTC)


def _parse_datetime(value: object) -> datetime | None:
    """Parse a timestamp-like value into an aware UTC datetime."""
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=UTC)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None
        return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


def _format_ct(dt: datetime) -> str:
    """Format a UTC datetime in Central Time."""
    local = dt.astimezone(CENTRAL_TZ)
    formatted = local.strftime("%Y-%m-%d %I:%M %p CT")
    if formatted[11] == "0":
        formatted = formatted[:11] + formatted[12:]
    return formatted


def _relative_age(target: datetime, reference: datetime | None = None) -> str:
    """Format a compact relative age string."""
    ref = reference or _utc_now()
    delta = ref - target
    seconds = int(delta.total_seconds())
    if seconds < 0:
        seconds = abs(seconds)
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def _prefix_label(track: str, tier: str) -> str:
    """Build the compact tier/track prefix."""
    tier_text = tier.strip().lower().replace("tier_", "T")
    if tier_text.startswith("t") and tier_text[1:].isdigit():
        tier_label = tier_text.upper()
    elif tier_text.startswith("tier") and tier_text[-1:].isdigit():
        tier_label = tier_text.replace("tier", "T").upper()
    else:
        tier_label = tier_text.upper() if tier_text else "T?"

    track_label = TRACK_PREFIXES.get(track, track.replace("_", "/").upper() if track else "UNSPEC")
    return f"[{tier_label} {track_label}]"


def _source_label(posting: dict) -> str:
    """Render a short source label."""
    source = str(posting.get("source", "")).strip().lower()
    source_name = SOURCE_LABELS.get(source, source.replace("_", " ").title() if source else "")
    source_type = str(posting.get("source_type", "")).strip().lower()
    if not source_name:
        return ""
    if source_type == "direct":
        suffix = "direct ATS"
    elif source_type:
        suffix = source_type
    else:
        suffix = ""
    return f"{source_name} ({suffix})" if suffix else source_name


def _why_matched(posting: dict) -> str | None:
    """Compose a short why-matched line from keyword and track context."""
    parts: list[str] = []
    keyword = str(posting.get("matched_keyword", "")).strip()
    track = str(posting.get("track", "")).strip()

    if keyword:
        parts.append(keyword)

    if track and track in TRACK_PREFIXES:
        track_context = f"{track.replace('_', ' ')} track"
        if track_context not in parts:
            parts.append(track_context)

    if not parts:
        return None
    return ", ".join(parts[:2])


def _split_signals(raw: object) -> list[str]:
    """Split a skills-like field into a compact list of signals."""
    if raw in (None, ""):
        return []
    if isinstance(raw, list):
        values = raw
    else:
        text = str(raw)
        values = re.split(r"[\n,;/]+", text)

    cleaned: list[str] = []
    for value in values:
        item = re.sub(r"^[\-\*\u2022\s]+", "", str(value)).strip()
        item = re.sub(r"\s+", " ", item)
        if item and item not in cleaned:
            cleaned.append(item)
    return cleaned[:5]


def _prep_link(posting: dict) -> str:
    """Build the vault prep link from company metadata."""
    company_slug = str(posting.get("company_slug", "")).strip().lower()
    if company_slug:
        slug = company_slug
    else:
        company_name = str(posting.get("company_name", "")).strip().lower()
        slug = re.sub(r"[^a-z0-9]+", "-", company_name).strip("-")
    return f"Vault/companies/{slug or 'unknown'}.md"


def _timestamp_line(posting: dict) -> str | None:
    """Render posted/detected timestamp semantics."""
    posted_at = _parse_datetime(posting.get("posted_at"))
    if posted_at is not None:
        return f"Posted: {_format_ct(posted_at)} ({_relative_age(posted_at)})"

    first_seen_at = _parse_datetime(posting.get("first_seen_at"))
    if first_seen_at is not None:
        return f"Detected: {_format_ct(first_seen_at)} ({_relative_age(first_seen_at)})"

    return None


def _display_value(posting: dict, key: str) -> str:
    """Return a compact display value with an Unknown fallback."""
    value = str(posting.get(key, "")).strip()
    return value or "Unknown"


def format_alert(posting: dict) -> str:
    """Format a posting dict into a compact Discord message string."""
    emoji = TRACK_EMOJI.get(posting.get("track", ""), "\u26aa")
    prefix = _prefix_label(str(posting.get("track", "")), str(posting.get("tier", "")))
    title = _display_value(posting, "title")
    company_name = _display_value(posting, "company_name")
    header = f"{emoji} {prefix} {title} @ {company_name}"

    lines: list[str] = [header]

    timestamp_line = _timestamp_line(posting)
    if timestamp_line:
        lines.append(timestamp_line)

    source_line = _source_label(posting)
    if source_line:
        lines.append(f"Source: {source_line}")

    why_matched = _why_matched(posting)
    if why_matched:
        lines.append(f"Why matched: {why_matched}")

    skills = _split_signals(posting.get("key_skills") or posting.get("skills"))
    if skills:
        lines.append("Key skills:")
        lines.extend(f"- {skill}" for skill in skills)

    apply_url = str(posting.get("apply_url") or posting.get("url") or "").strip()
    if apply_url:
        lines.append(f"Apply: {apply_url}")

    lines.append(f"Prep: {_prep_link(posting)}")

    return "\n".join(lines)


async def send_alert(posting: dict) -> None:
    """Send a single alert via Discord webhook. Skip if WEBHOOK_URL not set."""
    if not WEBHOOK_URL:
        return

    message = format_alert(posting)
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(WEBHOOK_URL, json={"content": message})


async def send_batch_alerts(postings: list[dict]) -> None:
    """Send multiple alerts sequentially."""
    for posting in postings:
        await send_alert(posting)
