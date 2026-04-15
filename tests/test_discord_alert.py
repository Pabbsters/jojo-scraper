"""Tests for discord_alert module."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from config import TRACK_EMOJI
from discord_alert import format_alert


class TestFormatAlertAllTracks:
    """Verify emoji mapping for every track."""

    @pytest.mark.parametrize("track,emoji", list(TRACK_EMOJI.items()))
    def test_correct_emoji_for_track(self, track: str, emoji: str) -> None:
        posting = {
            "title": "ML Intern",
            "company_name": "Acme",
            "url": "https://example.com/job/1",
            "track": track,
        }
        result = format_alert(posting)
        assert result.startswith(f"{emoji} [")


class TestFormatAlertFullPosting:
    """Test format with all optional fields present."""

    def test_all_fields_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "discord_alert._utc_now",
            lambda: datetime(2026, 4, 14, 15, 35, tzinfo=timezone.utc),
            raising=False,
        )
        posting = {
            "title": "ML Engineer Intern",
            "company_name": "Anthropic",
            "url": "https://example.com/job/42",
            "apply_url": "https://example.com/job/42/apply",
            "track": "ai_data",
            "tier": "tier_1",
            "source": "greenhouse",
            "source_type": "direct",
            "matched_keyword": "machine learning",
            "key_skills": "Python, PyTorch, ML systems, APIs",
            "posted_at": "2026-04-14T12:35:00Z",
            "first_seen_at": 1713100500.0,
        }
        result = format_alert(posting)
        assert result.startswith("🔴 [T1 AI/DATA] ML Engineer Intern @ Anthropic")
        assert "Posted: 2026-04-14 7:35 AM CT (3h ago)" in result
        assert "Source: Greenhouse (direct ATS)" in result
        assert "Why matched: machine learning, ai data track" in result
        assert "Key skills:" in result
        assert "- Python" in result
        assert "- PyTorch" in result
        assert "- ML systems" in result
        assert "- APIs" in result
        assert "Apply: https://example.com/job/42/apply" in result
        assert "Prep: Vault/companies/anthropic.md" in result


class TestFormatAlertMissingOptionalFields:
    """Omit optional lines when values are missing or empty."""

    def test_no_optional_fields(self) -> None:
        posting = {
            "title": "SWE Intern",
            "company_name": "BigCo",
            "url": "https://example.com/job/99",
            "track": "swe",
            "tier": "tier_2",
            "first_seen_at": 1713000000.0,
        }
        result = format_alert(posting)
        assert result.startswith("🟠 [T2 SWE] SWE Intern @ BigCo")
        assert "Detected:" in result
        assert "Source:" not in result
        assert "Why matched: swe track" in result
        assert "Key skills:" not in result
        assert "Apply: https://example.com/job/99" in result
        assert "Prep: Vault/companies/bigco.md" in result
        assert "Link:" not in result


class TestFormatAlertHeaderNormalization:
    """Empty or missing header fields fall back to Unknown."""

    @pytest.mark.parametrize(
        "posting,expected",
        [
            (
                {
                    "title": "   ",
                    "company_name": "",
                    "url": "https://example.com/job/100",
                    "track": "swe",
                },
                "🟠 [T? SWE] Unknown @ Unknown",
            ),
            (
                {
                    "company_name": "  Acme  ",
                    "url": "https://example.com/job/101",
                    "track": "swe",
                },
                "🟠 [T? SWE] Unknown @ Acme",
            ),
        ],
    )
    def test_empty_or_missing_title_and_company_use_unknown(
        self, posting: dict, expected: str
    ) -> None:
        result = format_alert(posting)
        assert result.startswith(expected)


class TestFormatAlertUnknownTrack:
    """Unknown or missing track falls back to white circle."""

    def test_unknown_track_uses_default_emoji(self) -> None:
        posting = {
            "title": "Intern",
            "company_name": "X",
            "url": "https://x.com",
            "track": "nonexistent_track",
        }
        result = format_alert(posting)
        assert result.startswith("\u26aa [T? ")

    def test_missing_track_uses_default_emoji(self) -> None:
        posting = {
            "title": "Intern",
            "company_name": "X",
            "url": "https://x.com",
            "track": "",
        }
        result = format_alert(posting)
        assert result.startswith("\u26aa [T? ")


class TestFormatAlertCompanySlug:
    """Verify prep doc slug generation."""

    def test_multi_word_company_name(self) -> None:
        posting = {
            "title": "Intern",
            "company_name": "Palo Alto Networks",
            "url": "https://x.com",
            "track": "swe",
        }
        result = format_alert(posting)
        assert "Vault/companies/palo-alto-networks.md" in result


class TestFormatAlertTimestampAndContext:
    """Timestamp semantics and context blocks follow the V1 contract."""

    def test_detected_when_posted_at_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "discord_alert._utc_now",
            lambda: datetime(2026, 4, 14, 23, 0, tzinfo=timezone.utc),
            raising=False,
        )
        posting = {
            "title": "Cloud Intern",
            "company_name": "AWS",
            "url": "https://aws.com/job/1",
            "track": "cloud_infra",
            "tier": "tier_1",
            "source": "ashby",
            "source_type": "direct",
            "matched_keyword": "cloud engineer",
            "key_skills": "AWS, Linux, networking",
            "first_seen_at": "2026-04-14T18:00:00Z",
        }
        result = format_alert(posting)

        assert "Detected: 2026-04-14 1:00 PM CT (5h ago)" in result
        assert "Why matched: cloud engineer" in result
        assert "Source: Ashby (direct ATS)" in result
        assert "Key skills:" in result
        assert result.count("- ") == 3

    def test_uses_track_context_when_keyword_missing(self) -> None:
        posting = {
            "title": "Platform Intern",
            "company_name": "Datadog",
            "url": "https://datadog.com/job/1",
            "track": "cloud_infra",
            "tier": "tier_1",
            "source": "greenhouse",
            "source_type": "fallback",
            "first_seen_at": 1713000000.0,
        }
        result = format_alert(posting)

        assert "Why matched: cloud infra track" in result
        assert "Source: Greenhouse (fallback)" in result
        assert "Apply: https://datadog.com/job/1" in result
