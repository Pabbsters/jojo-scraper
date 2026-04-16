# Top-50 Direct Seasonal Alerts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restrict Jojo alerts to a curated top-50 company universe using only direct careers sources, seasonal location rules, and a 72-hour freshness gate.

**Architecture:** Introduce a focused targeting policy layer that sits between source polling and persistence/alerting. Keep the existing source adapters, but only direct-source companies inside the curated registry are allowed to store and alert.

**Tech Stack:** Python 3.12, APScheduler, httpx, SQLite, pytest

---

## File Structure

- Modify: `config.py` — curated top-50 company registry, direct-source policy, season and employment constants, expanded role vocabulary
- Create: `targeting.py` — company/source/season/location/freshness gating helpers
- Modify: `main.py` — enforce targeting policy before DB writes and alerts, disable non-direct schedulers
- Modify: `matching.py` — allow `Bachelor's or Master's`, reject graduate-only requirements
- Modify: `tests/test_matching.py` — qualification and role-vocabulary coverage
- Modify: `tests/test_integration_pipeline.py` — direct-only, freshness, season, and company gating
- Modify: `docs/DESIGN.md` — point to the new active policy

## Tasks

- [ ] Add the new top-50 direct-only targeting spec and company registry.
- [ ] Add tests for season/location/freshness/direct-source gating.
- [ ] Implement the targeting helper layer and wire it into `main.py`.
- [ ] Expand role vocabulary and bachelor-vs-masters qualification handling.
- [ ] Remove non-direct alert sources from the scheduler path.
- [ ] Run the full test suite.
- [ ] Redeploy and verify live `/health` and `/feed`.
