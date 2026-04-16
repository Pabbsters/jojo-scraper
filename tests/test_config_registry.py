"""Tests for the top-company registry and direct source map."""

from __future__ import annotations

from config import (
    ASHBY_COMPANIES,
    DIRECT_ALERT_SOURCES,
    GREENHOUSE_COMPANIES,
    LEVER_COMPANIES,
    TIER1_COMPANIES,
    TIER1_SOURCE_PREFERENCES,
    build_coverage_report,
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
    assert TIER1_SOURCE_PREFERENCES["scale-ai"]["preferred_source"] == "greenhouse"
    assert TIER1_SOURCE_PREFERENCES["perplexity"]["preferred_source"] == "ashby"
    assert TIER1_SOURCE_PREFERENCES["palantir"]["preferred_source"] == "lever"


def test_company_lists_only_contain_registry_members() -> None:
    registry = {company["slug"] for company in TIER1_COMPANIES}
    for collection in (GREENHOUSE_COMPANIES, ASHBY_COMPANIES, LEVER_COMPANIES):
        for company in collection:
            assert company["slug"] in registry


def test_coverage_report_matches_registry_and_sources() -> None:
    registry = {company["slug"] for company in TIER1_COMPANIES}
    report = build_coverage_report()

    assert set(report["covered_companies"]) | set(report["uncovered_companies"]) == registry
    assert set(report["covered_companies"]) & set(report["uncovered_companies"]) == set()
    for source in report["preferred_source_by_company"].values():
        assert source in DIRECT_ALERT_SOURCES


def test_hidden_board_slug_overrides_are_present_for_verified_boards() -> None:
    greenhouse_overrides = {
        company["slug"]: company.get("board_slug")
        for company in GREENHOUSE_COMPANIES
    }
    assert greenhouse_overrides["hudsonrivertrading"] == "wehrtyou"
    assert greenhouse_overrides["scale-ai"] == "scaleai"
    assert greenhouse_overrides["dbtlabs"] == "dbtlabsinc"
    assert greenhouse_overrides["drw"] == "drweng"
    assert greenhouse_overrides["fiverings"] == "fiveringsllc"
