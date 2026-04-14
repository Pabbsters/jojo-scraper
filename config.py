"""Central configuration for jojo-scraper."""

from __future__ import annotations

import os


def _int_env(name: str, default: int) -> int:
    """Read an integer env var, falling back to *default* on bad input."""
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

# ── Intern title regex patterns ────────────────────────────────────────
INTERN_TITLE_PATTERNS: list[str] = [
    r"\bintern\b",
    r"\binternship\b",
    r"\bco-op\b",
    r"\bcoop\b",
    r"\bfellow\b",
    r"\bresidency\b",
    r"\bapprentice\b",
]

# ── Polling intervals (minutes) ────────────────────────────────────────
# JobSpy is slightly slower by default because LinkedIn/Glassdoor scraping
# is the most likely source to trigger anti-bot defenses.
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
