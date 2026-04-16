"""Tests for the matching / classification engine."""

from __future__ import annotations

import pytest

from config import TRACK_PRIORITY
from matching import classify_posting


# ── Basic classification ───────────────────────────────────────────────

class TestClassifyPosting:
    """classify_posting returns the highest-priority track that matches."""

    def test_ai_data_title_match(self):
        result = classify_posting("ML Engineer Intern - Summer 2026")
        assert result is not None
        assert result["track"] == "ai_data"
        assert result["priority"] == 0

    def test_swe_title_match(self):
        result = classify_posting("Software Engineer Intern - Backend")
        assert result is not None
        assert result["track"] == "swe"

    def test_sales_technical_match(self):
        result = classify_posting("Solutions Architect New Grad - Enterprise")
        assert result is not None
        assert result["track"] == "sales_technical"

    def test_consulting_match(self):
        result = classify_posting("Technology Consultant - New Grad")
        assert result is not None
        assert result["track"] == "consulting"

    def test_extras_match(self):
        result = classify_posting("Quantitative Developer Intern - Trading")
        assert result is not None
        assert result["track"] == "extras"

    def test_cloud_infra_match(self):
        result = classify_posting("Site Reliability Engineer Intern")
        assert result is not None
        assert result["track"] == "cloud_infra"

    def test_no_match_returns_none(self):
        result = classify_posting("Office Manager - HR Department")
        assert result is None

    def test_empty_title_returns_none(self):
        result = classify_posting("")
        assert result is None


# ── Priority ordering ──────────────────────────────────────────────────

class TestPriorityOrdering:
    """When multiple tracks could match, highest priority wins."""

    def test_ai_data_beats_swe(self):
        # "data engineer" is ai_data (priority 0), description mentions software
        result = classify_posting(
            "Data Engineer Intern",
            description="software engineer background preferred",
        )
        assert result is not None
        assert result["track"] == "ai_data"
        assert result["priority"] == 0

    def test_priority_value_is_index(self):
        result = classify_posting("DevOps Engineer Intern")
        assert result is not None
        assert result["track"] == "cloud_infra"
        assert result["priority"] == 5


# ── Case insensitivity ────────────────────────────────────────────────

class TestCaseInsensitivity:

    def test_uppercase_title(self):
        result = classify_posting("MACHINE LEARNING ENGINEER INTERN")
        assert result is not None
        assert result["track"] == "ai_data"

    def test_mixed_case_title(self):
        result = classify_posting("Software ENGINEER Intern")
        assert result is not None
        assert result["track"] == "swe"


# ── Description matching ──────────────────────────────────────────────

class TestDescriptionMatching:

    def test_keyword_in_description_only(self):
        result = classify_posting(
            "Intern - Open Position",
            description="Looking for a data scientist with Python experience",
        )
        assert result is not None
        assert result["track"] == "ai_data"

    def test_description_default_empty(self):
        result = classify_posting("Random Job Title")
        assert result is None


# ── Word boundary matching ────────────────────────────────────────────

class TestWordBoundary:

    def test_partial_word_does_not_match(self):
        # "consulting" should match, but "insult" should not match "consultant"
        result = classify_posting("Insultingly Bad Job Title")
        assert result is None

    def test_sre_matches_as_whole_word(self):
        result = classify_posting("SRE Intern - Production Systems")
        assert result is not None
        assert result["track"] == "cloud_infra"

    def test_sre_inside_word_no_match(self):
        # "sre" embedded in another word should not match
        result = classify_posting("Measureless Ocean Explorer")
        assert result is None


# ── Matched keyword returned ──────────────────────────────────────────

class TestMatchedKeyword:

    def test_returns_matched_keyword(self):
        result = classify_posting("ML Engineer Intern - NLP Team")
        assert result is not None
        assert result["matched_keyword"] == "ml engineer"

    def test_returns_first_matching_keyword_for_track(self):
        result = classify_posting("Deep Learning Research Scientist Intern")
        assert result is not None
        assert result["track"] == "ai_data"
        # Should match one of the ai_data keywords
        assert result["matched_keyword"] in [
            "deep learning", "research scientist",
        ]


class TestBachelorLevelFiltering:
    """Bachelor's filter should reject over-qualified/non-entry roles."""

    def test_coop_posting_returns_none(self):
        result = classify_posting("Software Engineer Co-op")
        assert result is None

    def test_phd_posting_returns_none(self):
        result = classify_posting(
            "Machine Learning Intern",
            description="PhD required for this role.",
        )
        assert result is None

    def test_senior_engineer_posting_returns_none(self):
        result = classify_posting("Senior Software Engineer Intern")
        assert result is None

    def test_intern_posting_matching_track_returns_match(self):
        result = classify_posting("Data Engineer Intern")
        assert result is not None
        assert result["track"] == "ai_data"

    def test_new_grad_posting_returns_match(self):
        result = classify_posting("Software Engineer New Grad")
        assert result is not None
        assert result["track"] == "swe"

    def test_bachelors_or_masters_requirement_returns_match(self):
        result = classify_posting(
            "Machine Learning Engineer Intern",
            description="Pursuing a Bachelor's or Master's degree in computer science.",
        )
        assert result is not None
        assert result["track"] == "ai_data"

    def test_masters_required_returns_none(self):
        result = classify_posting(
            "Machine Learning Engineer Intern",
            description="Master's degree required for this internship.",
        )
        assert result is None

    def test_seasonal_student_relevant_posting_returns_match(self):
        result = classify_posting(
            "Seasonal Software Engineer",
            description="Open to new grad and university hire candidates.",
        )
        assert result is not None
        assert result["track"] == "swe"

    def test_contract_student_relevant_posting_returns_match(self):
        result = classify_posting(
            "Contract Data Engineer",
            description="Open to new grad and university hire candidates.",
        )
        assert result is not None
        assert result["track"] == "ai_data"

    def test_temporary_student_relevant_posting_returns_match(self):
        result = classify_posting(
            "Temporary Data Engineer",
            description="The hiring manager is looking for university hire candidates.",
        )
        assert result is not None
        assert result["track"] == "ai_data"

    def test_plain_contract_posting_returns_none(self):
        result = classify_posting("Contract Data Engineer")
        assert result is None

    def test_seasonal_title_without_student_context_returns_none(self):
        result = classify_posting("Seasonal Software Engineer")
        assert result is None

    def test_experienced_contract_title_returns_none(self):
        result = classify_posting("Temporary Senior Software Engineer")
        assert result is None

    def test_no_intern_signal_in_title_returns_none(self):
        result = classify_posting(
            "Software Engineer",
            description="Software engineering role on the platform team.",
        )
        assert result is None

    def test_intern_signal_but_phd_in_description_returns_none(self):
        result = classify_posting(
            "Research Engineer Intern",
            description="Ideal candidate is pursuing a PhD in computer science.",
        )
        assert result is None


class TestCanonicalTrackVocabulary:
    def test_track_priority_order_is_unchanged(self):
        expected_order = [
            "ai_data",
            "swe",
            "sales_technical",
            "consulting",
            "extras",
            "cloud_infra",
        ]
        assert set(TRACK_PRIORITY) == set(expected_order)
        for earlier, later in zip(expected_order, expected_order[1:]):
            assert TRACK_PRIORITY.index(earlier) < TRACK_PRIORITY.index(later)

    def test_backend_engineer_maps_to_swe(self):
        result = classify_posting("Backend Engineer Intern - Summer 2026")
        assert result is not None
        assert result["track"] == "swe"

    def test_quant_researcher_maps_to_extras(self):
        result = classify_posting("Quant Researcher Intern - Summer 2026")
        assert result is not None
        assert result["track"] == "extras"

    def test_quant_trader_maps_to_extras(self):
        result = classify_posting("Quant Trader Intern - Summer 2026")
        assert result is not None
        assert result["track"] == "extras"

    def test_ai_product_manager_maps_to_ai_data(self):
        result = classify_posting("AI Product Manager Intern - Summer 2026")
        assert result is not None
        assert result["track"] == "ai_data"
