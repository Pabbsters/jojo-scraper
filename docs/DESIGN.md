# Jojo Alerts Design

**Status:** Active source of truth
**Last updated:** 2026-04-15

## Goal

Build an always-on Discord alert system that notifies Ruthwik about fresh,
bachelor-relevant internship, part-time, seasonal, temporary, or contract
roles at a curated top-50 company universe as soon as a direct
company-controlled source exposes the posting.

The system is optimized for:

- high alert precision
- readable mobile-first Discord messages
- fast detection for curated direct-source companies
- resume-actionable details

This v1 is **not** a newsletter system, knowledge-base system, or general
career platform. Those are later phases.

## User Profile

- UIUC Stats + CS + Data Science student
- Primary tracks: `ai_data`, `swe`
- Secondary tracks: `cloud_infra`, `sales_technical`, `consulting`, `extras`
- Wants alerts where both career fit and likely networking leverage matter

## Target Model

### Curated Top-50

The monitored universe is now a user-curated top-50 list built around FANG+,
AI labs, quant firms, data infra, and high-upside applied ML companies. The
registry is the only alertable company universe.

Some companies in the registry do not yet have direct adapters. Those
companies remain intentionally silent until a company-controlled source is
added. The system no longer falls back to GitHub, aggregators, Reddit, HN, or
other indirect discovery paths for alert generation.

## Source Selection Rule

For each company, use the **fastest reliable company-controlled source**.

Preferred order:

1. Direct ATS/API endpoint
2. Direct company careers page or company-controlled JSON feed

Important: only direct company-controlled sources may alert. If a company is in
the curated registry but has no supported direct adapter yet, it stays silent.

## Qualification Rules

A role should alert only if all of the following are true:

- company belongs to the curated top-50 registry
- title/description indicate a bachelor-relevant role
- posting matches one of Ruthwik’s target tracks
- posting is not excluded by advanced-degree or seniority rules
- posting has a trustworthy `posted_at` timestamp no older than 72 hours
- posting explicitly indicates `Summer 2026`, `Fall 2026`, or `Spring 2026`
- seasonal location rules are satisfied

### Included role signals

- intern
- internship
- part-time
- seasonal
- contract
- temporary

### Excluded role signals

- co-op
- new grad / recent graduate roles without internship-style scope
- PhD / master's-only / doctoral required roles
- senior/staff/principal/lead/manager/director roles
- experienced-hire roles that clearly expect beyond entry-level experience

Season rules:

- `Summer 2026` roles must be in the US
- `Fall 2026` and `Spring 2026` roles must be remote

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
- direct-source companies are explicitly represented in config
- alerts use only direct company-controlled sources
- non-bachelor and non-student-relevant roles are filtered out
- Discord alerts contain honest timestamps and concise key skills
- the system can be verified end to end with live `/health`, `/feed`, and
  a sample alert payload

## Non-Goals For V1

- newsletter generation
- broad Fortune 500 completeness
- fully automatic referral discovery
- full Vault enrichment automation
- social/news/community intelligence as an alert path

## Related Detailed Docs

- [Detailed v1 spec](./superpowers/specs/2026-04-14-jojo-alerts-v1-design.md)
- [Top-50 direct-seasonal spec](./superpowers/specs/2026-04-15-top50-direct-seasonal-alerts-design.md)
- [Top-50 implementation plan](./superpowers/plans/2026-04-15-top50-direct-seasonal-alerts-implementation.md)
