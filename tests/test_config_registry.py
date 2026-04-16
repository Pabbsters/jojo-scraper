"""Tests for the top-company registry and direct source map."""

from __future__ import annotations

from config import (
    ASHBY_COMPANIES,
    GREENHOUSE_COMPANIES,
    LEVER_COMPANIES,
    TIER1_COMPANIES,
    TIER1_SOURCE_PREFERENCES,
)


def test_top_company_registry_matches_unique_company_count() -> None:
    # ``top-companies.md`` is numbered to 60, but Databricks and Snowflake
    # are intentionally repeated in the Solutions Architect tier. The
    # deduplicated registry should therefore contain 58 unique companies.
    assert len(TIER1_COMPANIES) == 58


def test_top_company_registry_slugs_are_unique() -> None:
    slugs = [company["slug"] for company in TIER1_COMPANIES]
    assert len(slugs) == len(set(slugs))


def test_verified_direct_source_preferences_use_live_sources() -> None:
    assert TIER1_SOURCE_PREFERENCES["anthropic"]["preferred_source"] == "greenhouse"
    assert TIER1_SOURCE_PREFERENCES["google"]["preferred_source"] == "google"
    assert TIER1_SOURCE_PREFERENCES["openai"]["preferred_source"] == "ashby"
    assert "scale-ai" not in TIER1_SOURCE_PREFERENCES


def test_company_lists_only_contain_registry_members() -> None:
    registry = {company["slug"] for company in TIER1_COMPANIES}
    for collection in (GREENHOUSE_COMPANIES, ASHBY_COMPANIES, LEVER_COMPANIES):
        for company in collection:
            assert company["slug"] in registry
