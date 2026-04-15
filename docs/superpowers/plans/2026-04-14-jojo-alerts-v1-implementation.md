# Jojo Alerts V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a trustworthy tier-1 Discord alert pipeline that favors direct company-controlled sources, filters for bachelor-relevant roles, and sends compact timestamped alerts with useful key skills.

**Architecture:** The existing Python scraper remains the always-on service. We tighten config, matching, storage, and Discord formatting around a curated tier-1 company list first, then verify the live path before widening coverage.

**Tech Stack:** Python 3.12, APScheduler, httpx, SQLite, direct ATS/careers sources, pytest

---

## File Structure

- Modify: `config.py` — canonical tier-1 list, inclusion/exclusion vocabulary, source-priority metadata
- Modify: `matching.py` — bachelor-relevant qualification rules and company-tier-aware helpers
- Modify: `db.py` — store `posted_at`, `first_seen_at`, `tier`, `source_type`, `matched_keyword`, `key_skills`
- Modify: `discord_alert.py` — compact timestamped payload with key skills and prep link
- Modify: `main.py` — pass enriched metadata through the alert pipeline
- Modify: `sources/*.py` — surface source type and posted timestamps where available
- Modify: `tests/test_matching.py` — qualification rules and exclusions/inclusions
- Modify: `tests/test_db.py` — metadata storage assertions
- Modify: `tests/test_discord_alert.py` — payload formatting assertions
- Modify: `tests/test_feed.py` — feed contract for new metadata

## Task 1: Lock Canonical Product Vocabulary

**Files:**
- Modify: `config.py`
- Test: `tests/test_matching.py`

- [ ] **Step 1: Write the failing tests for tier vocabulary and qualification scope**

Add tests that assert:
- co-op titles return no match
- seasonal student-relevant roles can match
- contract student-relevant roles can match
- the canonical track order remains unchanged

- [ ] **Step 2: Run the focused test file to verify failures**

Run: `python3 -m pytest tests/test_matching.py -q`
Expected: failures for missing qualification behavior or mismatched assumptions.

- [ ] **Step 3: Update config constants**

Add or normalize:
- tier-1 curated company list
- include patterns for intern/new-grad/early-career/seasonal/contract/temporary
- explicit co-op exclusion patterns
- canonical track vocabulary comments

- [ ] **Step 4: Run the focused test file to verify it passes**

Run: `python3 -m pytest tests/test_matching.py -q`
Expected: all matching tests pass.

- [ ] **Step 5: Commit**

```bash
git add config.py tests/test_matching.py
git commit -m "feat: lock jojo alerts v1 vocabulary and qualification scope"
```

## Task 2: Make Qualification Rules Match The Product Goal

**Files:**
- Modify: `matching.py`
- Test: `tests/test_matching.py`

- [ ] **Step 1: Write the failing tests for new qualification semantics**

Add tests for:
- co-op exclusion
- seasonal inclusion when student-relevant
- contract inclusion when student-relevant
- senior contract exclusion
- PhD seasonal exclusion

- [ ] **Step 2: Run the focused tests to verify they fail for the right reason**

Run: `python3 -m pytest tests/test_matching.py -q`
Expected: failures tied to qualification logic, not syntax or import errors.

- [ ] **Step 3: Implement minimal matching changes**

Update `matching.py` so qualification logic:
- accepts bachelor-relevant seasonal/contract/temp roles
- excludes co-op explicitly
- preserves the advanced-degree and seniority filters

- [ ] **Step 4: Re-run matching tests**

Run: `python3 -m pytest tests/test_matching.py -q`
Expected: all matching tests pass.

- [ ] **Step 5: Commit**

```bash
git add matching.py tests/test_matching.py
git commit -m "feat: align qualification rules with jojo alerts v1"
```

## Task 3: Add Tier And Timestamp Metadata To Storage

**Files:**
- Modify: `db.py`
- Test: `tests/test_db.py`
- Test: `tests/test_feed.py`

- [ ] **Step 1: Write failing tests for stored metadata**

Add tests asserting stored postings preserve:
- `tier`
- `source_type`
- `matched_keyword`
- `key_skills`
- `posted_at`
- `first_seen_at`

- [ ] **Step 2: Run DB/feed tests to verify failure**

Run: `python3 -m pytest tests/test_db.py tests/test_feed.py -q`
Expected: failures showing the new fields are absent.

- [ ] **Step 3: Implement the schema and serialization changes**

Update `db.py` migration and insert/read paths so new metadata is stored and
returned cleanly in feed output.

- [ ] **Step 4: Re-run DB/feed tests**

Run: `python3 -m pytest tests/test_db.py tests/test_feed.py -q`
Expected: all DB/feed tests pass.

- [ ] **Step 5: Commit**

```bash
git add db.py tests/test_db.py tests/test_feed.py
git commit -m "feat: store jojo alert tier and timestamp metadata"
```

## Task 4: Define Tier-1 Source Preference

**Files:**
- Modify: `config.py`
- Modify: `main.py`
- Modify: relevant `sources/*.py`
- Test: create or extend source-selection tests where practical

- [ ] **Step 1: Write the failing test or fixture for source preference behavior**

Cover the rule:
- direct company-controlled source wins over GitHub/community source for tier 1

- [ ] **Step 2: Run the relevant test target to verify failure**

Run: `python3 -m pytest tests/ -q`
Expected: targeted failure or absence of the behavior.

- [ ] **Step 3: Implement source-preference metadata**

Add a per-company registry or equivalent configuration that records:
- company tier
- preferred direct source
- allowed fallbacks
- source type label used in alerts

- [ ] **Step 4: Re-run tests**

Run: `python3 -m pytest tests/ -q`
Expected: suite passes with source-preference logic preserved.

- [ ] **Step 5: Commit**

```bash
git add config.py main.py sources tests
git commit -m "feat: prefer direct sources for tier-1 jojo alerts"
```

## Task 5: Make Discord Alerts Readable And Resume-Actionable

**Files:**
- Modify: `discord_alert.py`
- Test: `tests/test_discord_alert.py`

- [ ] **Step 1: Write failing tests for the new alert payload**

Cover:
- `Posted:` formatting when `posted_at` exists
- `Detected:` formatting when only `first_seen_at` exists
- tier/track prefix rendering
- key-skills block
- concise source label

- [ ] **Step 2: Run the alert tests to verify failure**

Run: `python3 -m pytest tests/test_discord_alert.py -q`
Expected: formatting failures against the old payload shape.

- [ ] **Step 3: Implement minimal payload formatting**

Update `discord_alert.py` to render:
- concise header
- CT timestamp plus relative age
- source label
- why-matched line
- 3-5 key skills
- apply link
- prep link

- [ ] **Step 4: Re-run alert tests**

Run: `python3 -m pytest tests/test_discord_alert.py -q`
Expected: all alert-format tests pass.

- [ ] **Step 5: Commit**

```bash
git add discord_alert.py tests/test_discord_alert.py
git commit -m "feat: add timestamped resume-actionable jojo alerts"
```

## Task 6: Thread New Metadata Through The Main Pipeline

**Files:**
- Modify: `main.py`
- Modify: `matching.py`
- Modify: `discord_alert.py`
- Test: relevant existing tests

- [ ] **Step 1: Write failing integration-oriented tests or extend existing ones**

Assert that the pipeline can carry:
- tier
- matched keyword
- key skills
- timestamp fields
- source type

- [ ] **Step 2: Run the relevant tests to verify failure**

Run: `python3 -m pytest tests/ -q`
Expected: failures tied to missing propagation.

- [ ] **Step 3: Implement the minimal pipeline wiring**

Update `main.py` so classified postings pass enriched metadata into:
- DB persistence
- feed output
- Discord formatting

- [ ] **Step 4: Re-run the full test suite**

Run: `python3 -m pytest tests/ -q`
Expected: full suite passes.

- [ ] **Step 5: Commit**

```bash
git add main.py matching.py discord_alert.py tests
git commit -m "feat: thread jojo alert metadata through pipeline"
```

## Task 7: Verify Live Behavior

**Files:**
- Modify only if verification exposes a real issue

- [ ] **Step 1: Redeploy the updated service**

Use ComputeEdge with the canonical repo and existing deployment target.

- [ ] **Step 2: Verify health and feed**

Run:
- `curl http://159.69.150.218/health`
- `curl "http://159.69.150.218/feed?since=0"`

Expected:
- health returns `{"status":"ok"}`
- feed returns postings including the new metadata fields

- [ ] **Step 3: Verify alert rendering**

Confirm at least one live or test-triggered Discord alert shows:
- correct tier/track prefix
- honest timestamp label
- concise skills
- apply link

- [ ] **Step 4: Run stability check**

Use ComputeEdge monitor and direct checks to confirm:
- acceptable RAM
- acceptable CPU
- healthy service

- [ ] **Step 5: Commit any verification-driven fix**

```bash
git add .
git commit -m "fix: address live verification issues for jojo alerts v1"
```

## Task 8: Expand Only After Tier 1 Is Trusted

**Files:**
- Modify future config/docs as needed

- [ ] **Step 1: Review tier-1 outcomes**

Check:
- false positives
- missing desired companies
- weak skill extraction
- slow source paths

- [ ] **Step 2: Decide next expansion target**

Choose one:
- more direct tier-1 sources
- broader tier-2 companies
- referral-optimized reshaping of the curated list

- [ ] **Step 3: Write a separate follow-up plan before expanding**

Do not mix broader expansion back into the tier-1 stabilization effort.
