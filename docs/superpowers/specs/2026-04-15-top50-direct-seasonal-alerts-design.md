# Jojo Top-50 Direct Seasonal Alerts Design

**Status:** Approved for implementation
**Last updated:** 2026-04-15

## Goal

Refocus Jojo into a strict, high-signal alert system that monitors only a
curated top-50 company universe through direct careers sources and pings Ruthwik
only for fresh, bachelor-eligible roles that match his target career paths.

## Product Rules

- Only direct company-controlled sources may generate alerts.
- No GitHub repos, community sources, aggregators, or indirect boards may alert.
- Only the curated top-50 company list is in scope for monitoring.
- Alerts require a trustworthy source `posted_at` timestamp.
- Alerts only fire when the posting is at most 72 hours old.

## Seasonal Rules

- `Summer 2026` alerts:
  - US-only
  - internship, part-time, or contract only
- `Spring 2026` and `Fall 2026` alerts:
  - remote only
  - internship, part-time, or contract only

If a posting does not explicitly indicate `Summer 2026`, `Spring 2026`, or
`Fall 2026`, it should not alert.

## Qualification Rules

- Allow bachelor's-eligible roles for STEM students.
- Allow postings that say `Bachelor's or Master's`.
- Reject postings that require:
  - Master's
  - MS
  - PhD
  - doctoral study
  - postdoc / post-doctoral background
- Reject clearly graduate-only or advanced-degree-only research roles.

## Role Scope

The alert pipeline should include roles matching:

- Python Engineer
- C/C++ Engineer
- Backend Engineer
- Data Engineer
- Data Scientist
- ML Engineer
- AI Engineer
- ML/AI Researcher
- LLM Engineer
- Deep Learning
- Model Training / Inference
- Computer Vision
- MLOps
- ML Infrastructure
- Search Systems
- Solutions Architect / FDE
- Quant Researcher
- Quant Trader / Trading
- Quant Developer
- Quantitative Analyst
- AI Product Manager
- SWE when aligned with those paths

## Company Universe

Use a curated top-50 company registry driven by the user's ranking and explicit
company requests. This registry is the only alertable universe.

The implementation may keep some companies in the target registry before a
direct adapter exists, but unsupported companies must remain silent rather than
falling back to indirect sources.

## Operational Constraint

Direct adapters currently exist for only part of the target universe. The
system should:

- alert only for supported direct-source companies
- silently ignore unsupported companies for now
- preserve the curated target registry so future adapters can activate those
  companies without changing product rules

## Success Criteria

The system is successful when:

- non-direct sources no longer trigger alerts
- only curated top-50 companies are alertable
- season and location rules are enforced
- stale postings older than 72 hours do not alert
- postings without trustworthy `posted_at` do not alert
- live `/feed` and Discord alerts reflect the tightened policy
