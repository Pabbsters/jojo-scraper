"""Central configuration for jojo-scraper."""

from __future__ import annotations

import os


def _int_env(name: str, default: int) -> int:
    """Read an integer env var and fall back to *default* if unset/invalid."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default

# ── Track priority (index = priority, lower = higher) ──────────────────
TRACK_PRIORITY: list[str] = [
    "ai_data",
    "swe",
    "sales_technical",
    "consulting",
    "extras",
    "cloud_infra",
]

# ── Track emoji mapping ────────────────────────────────────────────────
TRACK_EMOJI: dict[str, str] = {
    "ai_data": "\U0001f534",         # red circle
    "swe": "\U0001f7e0",             # orange circle
    "sales_technical": "\U0001f7e1",  # yellow circle
    "consulting": "\U0001f535",       # blue circle
    "extras": "\U0001f7e2",           # green circle
    "cloud_infra": "\u26aa",          # white circle
}

# ── Track keywords (word-boundary matched) ─────────────────────────────
TRACK_KEYWORDS: dict[str, list[str]] = {
    "ai_data": [
        "ai engineer", "ml engineer", "machine learning", "data engineer",
        "data scientist", "nlp engineer", "mlops", "computer vision",
        "research engineer", "research scientist", "applied scientist",
        "data science", "deep learning", "artificial intelligence",
        "context engineer", "ai reliability", "decision scientist",
        "analytics engineer", "data analyst", "product intelligence",
        "business intelligence", "quantitative ux",
        "natural language processing",
    ],
    "swe": [
        "software engineer", "software developer", "full stack", "fullstack",
        "full-stack", "frontend engineer", "backend engineer",
        "embedded systems", "system architect", "mobile developer",
        "ios developer", "android developer", "swe intern",
        "software engineering",
    ],
    "sales_technical": [
        "sales engineer", "solutions architect", "customer engineer",
        "technical writer", "developer advocate", "developer relations",
        "developer experience", "technical evangelist", "pre-sales",
    ],
    "consulting": [
        "consultant", "consulting", "strategy analyst",
        "management consultant", "technology consultant", "advisory",
    ],
    "extras": [
        "quant", "quantitative developer", "robotics", "fintech",
        "blockchain", "web3", "sales and trading", "trading", "actuary",
        "studio engineer", "trust and safety", "trust & safety",
    ],
    "cloud_infra": [
        "cloud engineer", "cloud security", "cybersecurity",
        "site reliability", "sre", "infrastructure engineer",
        "network engineer", "devops", "iot architect",
        "platform engineer", "security engineer", "cloud architect",
        "devsecops",
    ],
}

# ── Tier 1 curated company list ────────────────────────────────────────
TIER1_COMPANIES: list[dict[str, str]] = [
    {"slug": "amazon", "name": "Amazon"},
    {"slug": "microsoft", "name": "Microsoft"},
    {"slug": "google", "name": "Google"},
    {"slug": "apple", "name": "Apple"},
    {"slug": "meta", "name": "Meta"},
    {"slug": "nvidia", "name": "NVIDIA"},
    {"slug": "databricks", "name": "Databricks"},
    {"slug": "palantir", "name": "Palantir"},
    {"slug": "cloudflare", "name": "Cloudflare"},
    {"slug": "datadog", "name": "Datadog"},
    {"slug": "shopify", "name": "Shopify"},
    {"slug": "openai", "name": "OpenAI"},
    {"slug": "anthropic", "name": "Anthropic"},
    {"slug": "cohere", "name": "Cohere"},
    {"slug": "stripe", "name": "Stripe"},
    {"slug": "ramp", "name": "Ramp"},
    {"slug": "capitalone", "name": "Capital One"},
    {"slug": "jpmorganchase", "name": "JPMorgan Chase"},
    {"slug": "goldmansachs", "name": "Goldman Sachs"},
    {"slug": "janestreet", "name": "Jane Street"},
    {"slug": "citadel", "name": "Citadel"},
    {"slug": "twosigma", "name": "Two Sigma"},
    {"slug": "deshaw", "name": "D.E. Shaw"},
    {"slug": "netflix", "name": "Netflix"},
    {"slug": "spacex", "name": "SpaceX"},
]

# ── Tier 1 source preferences ─────────────────────────────────────────
# Keep these companies pinned to their company-controlled source first.
TIER1_SOURCE_PREFERENCES: dict[str, dict[str, str]] = {
    "openai": {"preferred_source": "ashby", "source_type": "direct"},
    "anthropic": {"preferred_source": "ashby", "source_type": "direct"},
    "cohere": {"preferred_source": "ashby", "source_type": "direct"},
    "databricks": {"preferred_source": "greenhouse", "source_type": "direct"},
    "palantir": {"preferred_source": "greenhouse", "source_type": "direct"},
    "cloudflare": {"preferred_source": "greenhouse", "source_type": "direct"},
    "datadog": {"preferred_source": "greenhouse", "source_type": "direct"},
    "citadel": {"preferred_source": "greenhouse", "source_type": "direct"},
    "janestreet": {"preferred_source": "greenhouse", "source_type": "direct"},
    "twosigma": {"preferred_source": "greenhouse", "source_type": "direct"},
    "deshaw": {"preferred_source": "greenhouse", "source_type": "direct"},
    "netflix": {"preferred_source": "lever", "source_type": "direct"},
    "spacex": {"preferred_source": "lever", "source_type": "direct"},
}

# ── Company board sources ──────────────────────────────────────────────
GREENHOUSE_COMPANIES: list[dict[str, str]] = [
    {"slug": "citadel", "name": "Citadel"},
    {"slug": "janestreet", "name": "Jane Street"},
    {"slug": "twosigma", "name": "Two Sigma"},
    {"slug": "deshaw", "name": "D.E. Shaw"},
    {"slug": "palantir", "name": "Palantir"},
    {"slug": "databricks", "name": "Databricks"},
    {"slug": "figma", "name": "Figma"},
    {"slug": "notion", "name": "Notion"},
    {"slug": "datadoghq", "name": "Datadog"},
    {"slug": "cloudflare", "name": "Cloudflare"},
    {"slug": "paloaltonetworks", "name": "Palo Alto Networks"},
    {"slug": "crowdstrike", "name": "CrowdStrike"},
]

ASHBY_COMPANIES: list[dict[str, str]] = [
    {"slug": "anthropic", "name": "Anthropic"},
    {"slug": "openai", "name": "OpenAI"},
    {"slug": "cohere", "name": "Cohere"},
    {"slug": "mistral", "name": "Mistral AI"},
]

LEVER_COMPANIES: list[dict[str, str]] = [
    {"slug": "netflix", "name": "Netflix"},
    {"slug": "spacex", "name": "SpaceX"},
    {"slug": "scaleai", "name": "Scale AI"},
]

# ── Reddit sources ─────────────────────────────────────────────────────
SUBREDDITS: list[str] = [
    "csMajors", "cscareerquestions", "internships", "leetcode",
    "datascience", "MachineLearning", "UIUC", "recruitinghell",
    "experienceddevs", "SoftwareEngineerJobs", "FAANGrecruiting",
    "SaaS", "jobs", "forhire",
]

# ── GitHub repos tracking internships ──────────────────────────────────
GITHUB_REPOS: list[str] = [
    "SimplifyJobs/Summer2026-Internships",
    "jobright-ai/2026-Internship",
    "speedyapply/2026-AI-College-Jobs",
]

# ── Intern / entry-level title patterns (must match one) ──────────────
INTERN_TITLE_PATTERNS: list[str] = [
    r"\bintern\b",
    r"\binternship\b",
    r"\bco-op\b",
    r"\bcoop\b",
    r"\bfellow\b",
    r"\bresidency\b",
    r"\bapprentice\b",
    r"\bnew grad\b",
    r"\bnew-grad\b",
    r"\bentry[- ]level\b",
    r"\bearly career\b",
    r"\bearly-career\b",
    r"\bcampus hire\b",
    r"\buniversity hire\b",
    r"\brecent graduate\b",
]

# ── Product vocabulary retained for future seasonal/contract support ───
SEASONAL_CONTRACT_TITLE_TERMS: list[str] = [
    r"\bseasonal\b",
    r"\bcontract\b",
    r"\btemporary\b",
]

# ── Title/description patterns that disqualify a posting ──────────────
# These are roles above bachelor's level or requiring advanced degrees.
EXCLUDE_PATTERNS: list[str] = [
    r"\bco[- ]?op\b",
    r"\bcoop\b",
    r"\bcooperative education\b",
    r"\bphd\b",
    r"\bph\.d\b",
    r"\bdoctoral\b",
    r"\bpostdoc\b",
    r"\bpost-doc\b",
    r"\bsenior\b",
    r"\bstaff engineer\b",
    r"\bprincipal engineer\b",
    r"\bdirector\b",
    r"\bvp of\b",
    r"\bhead of\b",
    r"\blead engineer\b",
    r"\bmanager\b",
    r"\b[5-9]\+\s*years\b",
    r"\b[1-9][0-9]\+\s*years\b",
]

# ── Polling intervals (minutes) ────────────────────────────────────────
# JobSpy runs a bit slower by default because LinkedIn/Glassdoor are the
# most likely sources to hit anti-bot/rate-limit issues.
POLL_INTERVAL_MINUTES: dict[str, int] = {
    "greenhouse": _int_env("POLL_GREENHOUSE_MINUTES", 15),
    "ashby": _int_env("POLL_ASHBY_MINUTES", 15),
    "lever": _int_env("POLL_LEVER_MINUTES", 15),
    "github": _int_env("POLL_GITHUB_MINUTES", 15),
    "jobspy": _int_env("POLL_JOBSPY_MINUTES", 45),
    "amazon": _int_env("POLL_AMAZON_MINUTES", 30),
    "apple": _int_env("POLL_APPLE_MINUTES", 30),
    "reddit": _int_env("POLL_REDDIT_MINUTES", 60),
    "workday": _int_env("POLL_WORKDAY_MINUTES", 60),
    "hn": _int_env("POLL_HN_MINUTES", 1440),
}
