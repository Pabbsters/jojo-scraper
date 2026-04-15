# Jojo Alerts V1 Design Spec

**Author**: Codex
**Date**: 2026-04-14
**Status**: Approved for planning

## Overview

Jojo Alerts V1 is an always-on Discord alerting system for Ruthwik Pabbu.
Its purpose is to detect new bachelor-relevant opportunities from a curated
set of high-priority companies and send clean, timestamped, mobile-readable
Discord messages fast enough to support immediate applications, outreach, and
resume tailoring.

This spec intentionally narrows scope. V1 is about alert quality and speed.
Newsletter drafting, broad company-universe discovery, and deep knowledge-base
automation are moved out of the critical path.

## Product Goal

Send high-confidence Discord alerts for bachelor-relevant internship,
new-grad, early-career, seasonal, temporary, or contract tech roles at
curated target companies as soon as the fastest reliable direct source shows
the job.

## User Context

- UIUC Stats + CS + Data Science student
- optimizing for both career fit and future networking leverage
- wants UIUC-friendly employers prioritized
- wants alerts that are useful for resume adjustment in the moment

## Tier Strategy

### Tier 1: Curated 25

Tier 1 is the must-watch company list:

1. Amazon
2. Microsoft
3. Google
4. Apple
5. Meta
6. NVIDIA
7. Databricks
8. Palantir
9. Cloudflare
10. Datadog
11. Shopify
12. OpenAI
13. Anthropic
14. Cohere
15. Stripe
16. Ramp
17. Capital One
18. JPMorgan Chase
19. Goldman Sachs
20. Jane Street
21. Citadel
22. Two Sigma
23. D. E. Shaw
24. Netflix
25. SpaceX

Rationale:

- high alignment with Ruthwik’s target tracks
- public UIUC-friendly recruiting/alumni signals
- high internship relevance
- realistic direct-source monitoring options

### Tier 2: Broader Target Universe

Expanded big tech, Fortune 500, fintech, cloud, consulting, and adjacent
employers. This tier matters, but it must not dilute the speed and precision
of tier 1.

### Tier 3: Discovery Sources

GitHub internship repos, aggregators, and community sources. These are useful
for discovery and future expansion but do not define the core v1 promise.

## Source Strategy

The system should not blindly prefer ATS over careers pages. Instead, each
company gets a source-of-truth rule:

- use the fastest reliable company-controlled source
- fall back only if the direct source is unavailable or too brittle

Priority order:

1. direct ATS/API feed
2. direct company careers page or company-controlled JSON feed
3. trusted fallback source
4. aggregator or GitHub/community discovery source

For tier 1, GitHub internship repos should not be the primary alert source.

## Qualification Rules

### Include

- intern
- internship
- new grad
- early career
- entry level
- recent graduate
- seasonal
- contract
- temporary

### Exclude

- co-op
- apprenticeship programs that require leaving school
- PhD/MS/doctoral required roles
- senior/staff/principal/lead/manager/director roles
- clearly experienced-hire postings

### Interpretation Rule

Treat bachelor-relevant roles as student-relevant roles. If a posting is
appropriate for someone pursuing a B.S. or just graduating from that path,
it should qualify even if it is not labeled with perfect campus wording.

## Track Model

Canonical track order:

1. `ai_data`
2. `swe`
3. `sales_technical`
4. `consulting`
5. `extras`
6. `cloud_infra`

Track naming in docs, code, tests, and alerts must match exactly.

## Alert Payload Contract

### Required fields

- tier label
- track label
- title
- company
- timestamp
- source
- short “why matched” explanation
- 3-5 key skills or hiring signals
- apply link
- prep link

### Timestamp semantics

The payload must distinguish between:

- `posted_at`: source-provided true posting time
- `first_seen_at`: scraper detection time

Display rules:

- If `posted_at` exists, show `Posted: <CT> (<relative age>)`
- If `posted_at` is missing, show `Detected: <CT> (<relative age>)`

### Example payload

```text
[T1 SWE] Software Engineer Intern @ Cloudflare
Posted: 2026-04-14 1:35 PM CT (2h ago)
Source: Greenhouse (direct ATS)
Why matched: swe, software engineer, backend

Key skills:
- Python
- distributed systems
- APIs
- networking

Apply: https://...
Prep: Vault/companies/cloudflare.md
```

### Payload principles

- concise enough to scan on a phone
- actionable enough to tailor a resume quickly
- honest about source and timestamp confidence
- free of long raw description text

## Data Model Changes

The posting storage model should include:

- `tier`
- `source_type`
- `matched_keyword`
- `key_skills`
- `posted_at`
- `first_seen_at`

This enables truthful Discord payloads and later analysis of source quality.

## Reliability Requirements

- tier-1 companies must have explicit source preference rules
- source fallback must be deterministic
- false positives from PhD/senior/co-op roles should be aggressively reduced
- skills extraction should prefer high-signal requirements over noisy prose

## Testing Requirements

V1 testing should emphasize:

- qualification logic
- co-op exclusion
- seasonal/contract inclusion when bachelor-relevant
- posted vs detected timestamp rendering
- per-tier payload formatting
- key-skills extraction quality
- source-priority behavior for tier 1

## Operational Verification

Before calling v1 complete, verify:

- `/health` works
- `/feed` exposes structured postings with the new metadata
- at least one sample Discord alert renders with the new compact format
- tier-1 direct sources are preferred over GitHub/community sources

## Out of Scope

- LinkedIn connection graph automation
- newsletter generation
- full Fortune 500 completeness
- knowledge-base enrichment as part of the tier-1 alert critical path
