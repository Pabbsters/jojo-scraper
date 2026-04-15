# Jojo Alerts V1 Design

**Status:** Active source of truth for v1
**Last updated:** 2026-04-14

## Goal

Build an always-on Discord alert system that notifies Ruthwik about new
bachelor-relevant internship, new-grad, early-career, seasonal, temporary,
or contract roles at a curated set of high-priority companies as soon as the
fastest reliable company-controlled source exposes the posting.

The system is optimized for:

- high alert precision
- readable mobile-first Discord messages
- fast detection for tier-1 companies
- resume-actionable details

This v1 is **not** a newsletter system, knowledge-base system, or general
career platform. Those are later phases.

## User Profile

- UIUC Stats + CS + Data Science student
- Primary tracks: `ai_data`, `swe`
- Secondary tracks: `cloud_infra`, `sales_technical`, `consulting`, `extras`
- Wants alerts where both career fit and likely networking leverage matter

## Tier Model

### Tier 1: Curated 25

These companies get the highest-trust alert path and the strongest effort on
speed, source quality, and filtering:

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

This list is chosen using a hybrid heuristic:

- strong career fit for Ruthwik
- public UIUC-friendly recruiting/alumni signals
- high internship/new-grad relevance
- feasible direct-source monitoring

### Tier 2: Extended Target Universe

Broader Fortune 500, big-tech, fintech, quant, cloud, AI, and consulting
coverage. Tier 2 is important, but it must not lower tier-1 quality.

### Tier 3: Discovery

Aggregators, GitHub repos, and community sources used for backfill or future
promotion into tier 1 or tier 2. These do not define the core “post ASAP”
promise for tier 1.

## Source Selection Rule

For each company, use the **fastest reliable company-controlled source**.

Preferred order:

1. Direct ATS/API endpoint
2. Direct company careers page or company-controlled JSON feed
3. High-quality fallback source
4. Aggregator or GitHub/community discovery source

Important: ATS is not always better than the careers page. The source of truth
for a company is whichever direct company-controlled source proves to expose the
role fastest and most reliably in practice.

## Qualification Rules

A role should alert only if all of the following are true:

- company belongs to an enabled target tier
- title/description indicate a bachelor-relevant role
- posting matches one of Ruthwik’s target tracks
- posting is not excluded by advanced-degree or seniority rules

### Included role signals

- intern
- internship
- new grad
- early career
- entry level
- recent graduate
- seasonal
- contract
- temporary

### Excluded role signals

- co-op
- apprenticeship programs that require leaving school full-time
- PhD/MS/doctoral required roles
- senior/staff/principal/lead/manager/director roles
- experienced-hire roles that clearly expect beyond entry-level experience

Interpretation rule:

`bachelor-relevant` means appropriate for a student currently pursuing a B.S.
or a very recent graduate from that same pipeline.

## Alert Contract

Alerts must be short, readable, and immediately useful on mobile.

### Required fields

- company
- title
- tier
- track
- source name
- apply URL
- source quality label
- timestamp
- 3-5 key skills or hiring signals

### Timestamp rule

If the source provides a real posting timestamp:

- show `Posted: <time in CT> (<relative age>)`

If the source does not provide a real posting timestamp:

- show `Detected: <time in CT> (<relative age>)`

The system must never pretend a first-seen timestamp is a true posted timestamp.

### Message shape

```text
[T1 AI/DATA] Machine Learning Intern @ Databricks
Posted: 2026-04-14 1:35 PM CT (2h ago)
Source: Greenhouse (direct ATS)
Why matched: ai_data, machine learning, research engineer

Key skills:
- Python
- PyTorch
- distributed systems
- data pipelines

Apply: https://...
Prep: Vault/companies/databricks.md
```

### Payload principles

- no walls of text
- no raw job description dumps
- no fake precision
- only the details needed to decide whether to apply, tailor, or network

## Data Model Requirements

Each stored posting should preserve:

- `source`
- `source_type`
- `company_slug`
- `company_name`
- `tier`
- `track`
- `posting_id`
- `title`
- `url`
- `description`
- `key_skills`
- `posted_at`
- `first_seen_at`
- `matched_keyword`

## Success Criteria

V1 is successful when:

- tier-1 companies are explicitly represented in config
- tier-1 alerts prefer direct company-controlled sources
- non-bachelor and non-student-relevant roles are filtered out
- Discord alerts contain honest timestamps and concise key skills
- the system can be verified end to end with live `/health`, `/feed`, and
  a sample alert payload

## Non-Goals For V1

- newsletter generation
- broad Fortune 500 completeness
- fully automatic referral discovery
- full Vault enrichment automation
- social/news/community intelligence as a primary alert path

## Related Detailed Docs

- [Detailed v1 spec](./superpowers/specs/2026-04-14-jojo-alerts-v1-design.md)
- [Implementation plan](./superpowers/plans/2026-04-14-jojo-alerts-v1-implementation.md)
