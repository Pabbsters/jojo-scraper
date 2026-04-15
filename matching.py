"""Track classification engine for job postings."""

from __future__ import annotations

import re
from typing import Optional

from config import (
    EXCLUDE_PATTERNS,
    INTERN_TITLE_PATTERNS,
    SEASONAL_CONTRACT_TITLE_TERMS,
    TRACK_KEYWORDS,
    TRACK_PRIORITY,
)

_TITLE_EXCLUDE_PATTERNS: list[str] = [
    r"\bsenior\b",
    r"\bstaff engineer\b",
    r"\bprincipal engineer\b",
    r"\bdirector\b",
    r"\bvp of\b",
    r"\bhead of\b",
    r"\blead engineer\b",
    r"\bmanager\b",
]

_COMBINED_EXCLUDE_PATTERNS: list[str] = [
    pattern
    for pattern in EXCLUDE_PATTERNS
    if pattern not in _TITLE_EXCLUDE_PATTERNS
]


def _matches_any(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _is_bachelor_level(title: str, description: str) -> bool:
    """Return True if the posting is appropriate for a bachelor's student.

    Requires no disqualifying patterns (PhD required, senior, 5+ years, etc.)
    and either:
    - a direct intern/entry-level signal, or
    - a seasonal/contract/temporary title term plus a student-relevant signal.
    """
    title_lower = title.lower()
    combined_lower = f"{title} {description}".lower()

    # Seniority signals should be title-based so normal prose like
    # "hiring manager" or "reports to the director" in descriptions does not
    # incorrectly reject an otherwise valid role.
    if _matches_any(_TITLE_EXCLUDE_PATTERNS, title_lower):
        return False

    # Hard exclusions that legitimately can appear in descriptions too.
    if _matches_any(_COMBINED_EXCLUDE_PATTERNS, combined_lower):
        return False

    # Standard internship / new-grad / entry-level wording still qualifies.
    if _matches_any(INTERN_TITLE_PATTERNS, combined_lower):
        return True

    # Seasonal / contract / temporary roles only qualify when the posting
    # also makes the student-facing intent explicit.
    if _matches_any(SEASONAL_CONTRACT_TITLE_TERMS, title_lower) and _matches_any(
        INTERN_TITLE_PATTERNS, combined_lower
    ):
        return True

    return False


def classify_posting(title: str, description: str = "") -> Optional[dict]:
    """Classify a posting into the highest-priority matching track.

    Only returns a match for postings appropriate for a bachelor's student
    (intern, new grad, entry-level, no PhD/senior requirements).

    Returns:
        A dict with keys ``track``, ``priority``, and ``matched_keyword``
        for the highest-priority match, or ``None`` if nothing matches.
    """
    if not title and not description:
        return None

    if not _is_bachelor_level(title, description):
        return None

    combined = f"{title} {description}".lower()

    for priority, track in enumerate(TRACK_PRIORITY):
        keywords = TRACK_KEYWORDS.get(track, [])
        for keyword in keywords:
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, combined):
                return {
                    "track": track,
                    "priority": priority,
                    "matched_keyword": keyword,
                }

    return None
