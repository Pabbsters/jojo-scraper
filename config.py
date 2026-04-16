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
        "llm engineer", "ai researcher", "ml researcher",
        "ai product manager", "model training", "model inference",
        "inference engineer", "search systems", "search system",
        "search relevance", "ml infrastructure",
    ],
    "swe": [
        "software engineer", "software developer", "full stack", "fullstack",
        "full-stack", "frontend engineer", "backend engineer",
        "embedded systems", "system architect", "mobile developer",
        "ios developer", "android developer", "swe intern",
        "software engineering", "python engineer", "c++ engineer",
        "c/c++ engineer", "cpp engineer",
    ],
    "sales_technical": [
        "sales engineer", "solutions architect", "customer engineer",
        "technical writer", "developer advocate", "developer relations",
        "developer experience", "technical evangelist", "pre-sales",
        "forward deployed engineer", "field deployment engineer", "fde",
    ],
    "consulting": [
        "consultant", "consulting", "strategy analyst",
        "management consultant", "technology consultant", "advisory",
    ],
    "extras": [
        "quant", "quantitative developer", "robotics", "fintech",
        "blockchain", "web3", "sales and trading", "trading", "actuary",
        "studio engineer", "trust and safety", "trust & safety",
        "quant researcher", "quant research", "quant trader",
        "quant trading", "quant developer", "quantitative analyst",
    ],
    "cloud_infra": [
        "cloud engineer", "cloud security", "cybersecurity",
        "site reliability", "sre", "infrastructure engineer",
        "network engineer", "devops", "iot architect",
        "platform engineer", "security engineer", "cloud architect",
        "devsecops",
    ],
}

# ── Curated top-50 company list ────────────────────────────────────────
# The registry reflects the user's ranked target universe for direct-careers
# monitoring. Some entries are not yet adapter-backed and remain intentionally
# silent until a direct source is added.
TIER1_COMPANIES: list[dict[str, str]] = [
    {"slug": "janestreet", "name": "Jane Street"},
    {"slug": "hudsonrivertrading", "name": "Hudson River Trading"},
    {"slug": "deshaw", "name": "D.E. Shaw"},
    {"slug": "citadel", "name": "Citadel"},
    {"slug": "anthropic", "name": "Anthropic"},
    {"slug": "openai", "name": "OpenAI"},
    {"slug": "imc", "name": "IMC"},
    {"slug": "optiver", "name": "Optiver"},
    {"slug": "meta", "name": "Meta"},
    {"slug": "apple", "name": "Apple"},
    {"slug": "google", "name": "Google"},
    {"slug": "nvidia", "name": "NVIDIA"},
    {"slug": "microsoft", "name": "Microsoft"},
    {"slug": "amazon", "name": "Amazon"},
    {"slug": "bytedance", "name": "ByteDance"},
    {"slug": "databricks", "name": "Databricks"},
    {"slug": "snowflake", "name": "Snowflake"},
    {"slug": "stripe", "name": "Stripe"},
    {"slug": "perplexity", "name": "Perplexity"},
    {"slug": "xai", "name": "xAI"},
    {"slug": "scaleai", "name": "Scale AI"},
    {"slug": "cohere", "name": "Cohere"},
    {"slug": "waymo", "name": "Waymo"},
    {"slug": "tesla", "name": "Tesla"},
    {"slug": "mistral", "name": "Mistral AI"},
    {"slug": "linkedin", "name": "LinkedIn"},
    {"slug": "intuit", "name": "Intuit"},
    {"slug": "snap", "name": "Snap"},
    {"slug": "palantir", "name": "Palantir"},
    {"slug": "uber", "name": "Uber"},
    {"slug": "airbnb", "name": "Airbnb"},
    {"slug": "doordash", "name": "DoorDash"},
    {"slug": "spotify", "name": "Spotify"},
    {"slug": "salesforce", "name": "Salesforce"},
    {"slug": "twosigma", "name": "Two Sigma"},
    {"slug": "jumptrading", "name": "Jump Trading"},
    {"slug": "drw", "name": "DRW"},
    {"slug": "akuna", "name": "Akuna Capital"},
    {"slug": "fiverings", "name": "Five Rings"},
    {"slug": "millennium", "name": "Millennium"},
    {"slug": "point72", "name": "Point72 Cubist"},
    {"slug": "sig", "name": "SIG"},
    {"slug": "confluent", "name": "Confluent"},
    {"slug": "mongodb", "name": "MongoDB"},
    {"slug": "elastic", "name": "Elastic"},
    {"slug": "dbtlabs", "name": "dbt Labs"},
    {"slug": "fivetran", "name": "Fivetran"},
    {"slug": "anyscale", "name": "Anyscale"},
    {"slug": "wandb", "name": "Weights & Biases"},
    {"slug": "bloomberg", "name": "Bloomberg"},
]

TARGET_COMPANY_SLUGS: set[str] = {company["slug"] for company in TIER1_COMPANIES}

# ── Tier 1 source preferences ─────────────────────────────────────────
# Keep these companies pinned to their company-controlled source.
TIER1_SOURCE_PREFERENCES: dict[str, dict[str, str]] = {
    "amazon": {"preferred_source": "amazon", "source_type": "direct"},
    "apple": {"preferred_source": "apple", "source_type": "direct"},
    "openai": {"preferred_source": "ashby", "source_type": "direct"},
    "anthropic": {"preferred_source": "ashby", "source_type": "direct"},
    "cohere": {"preferred_source": "ashby", "source_type": "direct"},
    "mistral": {"preferred_source": "ashby", "source_type": "direct"},
    "databricks": {"preferred_source": "greenhouse", "source_type": "direct"},
    "palantir": {"preferred_source": "greenhouse", "source_type": "direct"},
    "citadel": {"preferred_source": "greenhouse", "source_type": "direct"},
    "janestreet": {"preferred_source": "greenhouse", "source_type": "direct"},
    "twosigma": {"preferred_source": "greenhouse", "source_type": "direct"},
    "deshaw": {"preferred_source": "greenhouse", "source_type": "direct"},
    "scaleai": {"preferred_source": "lever", "source_type": "direct"},
    "nvidia": {"preferred_source": "workday", "source_type": "direct"},
    "tesla": {"preferred_source": "workday", "source_type": "direct"},
}

# ── Company board sources ──────────────────────────────────────────────
GREENHOUSE_COMPANIES: list[dict[str, str]] = [
    {"slug": "citadel", "name": "Citadel"},
    {"slug": "janestreet", "name": "Jane Street"},
    {"slug": "twosigma", "name": "Two Sigma"},
    {"slug": "deshaw", "name": "D.E. Shaw"},
    {"slug": "palantir", "name": "Palantir"},
    {"slug": "databricks", "name": "Databricks"},
]

ASHBY_COMPANIES: list[dict[str, str]] = [
    {"slug": "anthropic", "name": "Anthropic"},
    {"slug": "openai", "name": "OpenAI"},
    {"slug": "cohere", "name": "Cohere"},
    {"slug": "mistral", "name": "Mistral AI"},
]

LEVER_COMPANIES: list[dict[str, str]] = [
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

# ── Source and title policy ────────────────────────────────────────────
DIRECT_ALERT_SOURCES: set[str] = {
    "greenhouse",
    "ashby",
    "lever",
    "amazon",
    "apple",
    "workday",
}

# ── Intern / entry-level title patterns for bachelor-level intent ─────
INTERN_TITLE_PATTERNS: list[str] = [
    r"\bintern\b",
    r"\binternship\b",
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

# ── Alertable employment/title vocabulary ──────────────────────────────
ALERT_TITLE_PATTERNS: list[str] = [
    *INTERN_TITLE_PATTERNS,
    r"\bco-op\b",
    r"\bcoop\b",
    r"\bfellow\b",
    r"\bresidency\b",
    r"\bapprentice\b",
    r"\bpart[- ]time\b",
    r"\bcontract\b",
    r"\bcontractor\b",
    r"\bseasonal\b",
    r"\btemporary\b",
    r"\btemp\b",
]

STUDENT_SIGNAL_PATTERNS: list[str] = [
    *INTERN_TITLE_PATTERNS,
    r"\bstudent\b",
    r"\bundergraduate\b",
    r"\bbachelor'?s\b",
    r"\bbachelor’s\b",
    r"\bb\.s\.\b",
    r"\bbs\b",
    r"\buniversity\b",
    r"\bcampus\b",
    r"\bcurrently pursuing\b",
    r"\benrolled\b",
]

SEASONAL_CONTRACT_TITLE_TERMS: list[str] = [
    r"\bseasonal\b",
    r"\bcontract\b",
    r"\bcontractor\b",
    r"\bpart[- ]time\b",
    r"\btemporary\b",
    r"\btemp\b",
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
    r"\bmaster'?s(?: degree)? required\b",
    r"\bmaster'?s(?: degree)? preferred\b",
    r"\bm\.?s\.?(?: degree)? required\b",
    r"\bm\.?s\.?(?: degree)? preferred\b",
    r"\bgraduate student\b",
    r"\bgraduate-level\b",
    r"\bpostgraduate\b",
    r"\bcurrently pursuing (?:a )?master'?s\b",
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

ALLOWED_EMPLOYMENT_PATTERNS: list[str] = [
    r"\bintern\b",
    r"\binternship\b",
    r"\bpart[- ]time\b",
    r"\bcontract\b",
    r"\bcontractor\b",
    r"\bseasonal\b",
    r"\btemporary\b",
    r"\btemp\b",
]

REMOTE_PATTERNS: list[str] = [
    r"\bremote\b",
    r"\bwork from home\b",
    r"\bdistributed\b",
    r"\bvirtual\b",
]

US_PATTERNS: list[str] = [
    r"\bunited states\b",
    r"\busa\b",
    r"\bu\.s\.\b",
    r"\bus-based\b",
    r"\bus only\b",
    r"\bremote - united states\b",
    r"\bremote, united states\b",
    r"\bcalifornia\b",
    r"\bwashington\b",
    r"\bnew york\b",
    r"\billinois\b",
    r"\bmassachusetts\b",
    r"\btexas\b",
    r"\bvirginia\b",
    r"\bgeorgia\b",
    r"\bflorida\b",
    r"\bnorth carolina\b",
    r"\bseattle\b",
    r"\bsan francisco\b",
    r"\bnew york city\b",
    r",\s*(?:AL|AK|AZ|AR|CA|CO|CT|DC|DE|FL|GA|HI|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)\b",
]

SEASON_PATTERNS: dict[str, list[str]] = {
    "summer_2026": [
        r"\bsummer\s+2026\b",
        r"\b2026\s+summer\b",
    ],
    "fall_2026": [
        r"\bfall\s+2026\b",
        r"\b2026\s+fall\b",
        r"\bautumn\s+2026\b",
        r"\b2026\s+autumn\b",
    ],
    "spring_2026": [
        r"\bspring\s+2026\b",
        r"\b2026\s+spring\b",
    ],
}

SEASON_LOCATION_RULES: dict[str, str] = {
    "summer_2026": "us",
    "fall_2026": "remote",
    "spring_2026": "remote",
}

MAX_POST_AGE_HOURS = 72

# ── Polling intervals (minutes) ────────────────────────────────────────
POLL_INTERVAL_MINUTES: dict[str, int] = {
    "greenhouse": _int_env("POLL_GREENHOUSE_MINUTES", 15),
    "ashby": _int_env("POLL_ASHBY_MINUTES", 15),
    "lever": _int_env("POLL_LEVER_MINUTES", 15),
    "amazon": _int_env("POLL_AMAZON_MINUTES", 30),
    "apple": _int_env("POLL_APPLE_MINUTES", 30),
    "workday": _int_env("POLL_WORKDAY_MINUTES", 60),
}
