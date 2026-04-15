# Jojo Alerts V1 Plan Overview

**Status:** Active source of truth for execution order
**Last updated:** 2026-04-14

## Objective

Deliver a high-precision Discord alert pipeline for Ruthwik’s curated tier-1
company list before expanding to broader discovery, newsletters, or knowledge
base workflows.

## Execution Order

1. Lock the tiered company model in docs and config
2. Normalize bachelor-relevant qualification rules
3. Define per-company source preference for tier 1
4. Upgrade stored posting metadata for honest timestamps and tier labels
5. Upgrade Discord payload for readability and resume actionability
6. Verify end-to-end behavior with focused tests and live checks
7. Only then expand beyond tier 1

## What Must Be True Before Expansion

- tier-1 list is explicit and reviewable
- direct company-controlled sources are preferred where available
- alerts exclude co-ops and advanced-degree/senior roles
- alerts include timestamp, source, track, and key skills
- docs, code, and live behavior use the same vocabulary

## Deferred Work

- newsletter generation
- broad Fortune 500 sweep
- full NanoClaw enrichment automation
- discovery-heavy GitHub/community sourcing as a primary signal

## Detailed Plan

Use the detailed implementation plan for actual execution:

- [docs/superpowers/plans/2026-04-14-jojo-alerts-v1-implementation.md](./superpowers/plans/2026-04-14-jojo-alerts-v1-implementation.md)
