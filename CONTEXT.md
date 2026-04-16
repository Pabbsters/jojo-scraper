# Jojo Scraper — Context for Codex

This is the standalone deploy repo for the jojo internship scraper. It is a copy of
`/nanoclaw/scraper/` on branch `feat/jojo-scraper` of `github.com/Pabbsters/nanoclaw`.

## Live Deployment

| Key | Value |
|-----|-------|
| URL | `http://159.69.150.218` |
| Health | `GET http://159.69.150.218/health` |
| Feed | `GET http://159.69.150.218/feed?since=<unix_ts>` |
| Provider | Hetzner (via ComputeEdge MCP) |
| Deployment ID | `ce-hetzner-815715f4` |
| Cost | $3.49/mo |

## Repos

| Repo | Purpose |
|------|---------|
| `github.com/Pabbsters/jojo-scraper` | **This repo** — what's deployed to Hetzner |
| `github.com/Pabbsters/nanoclaw` branch `feat/jojo-scraper` | Source of truth — also has docs + NanoClaw tasks |

When making changes, apply them here AND in `nanoclaw/scraper/` to keep them in sync.

## What This Does

Always-on Python scraper that:
- Polls direct company-controlled sources (Greenhouse, Ashby, Lever, Amazon, Apple, Workday)
- Restricts alerts to a curated top-50 company universe with season, freshness, and bachelor's-level policy gates
- Sends Discord webhook alerts (Format B rich card) for new matches
- Exposes `GET /feed` JSON endpoint for NanoClaw AI tasks to consume

## Architecture

```
main.py          — asyncio entry point, APScheduler loop
config.py        — company lists, role keywords, poll intervals
db.py            — SQLite dedup (seen postings)
discord_alert.py — Discord webhook sender
matching.py      — classify posting against career tracks
feed.py          — HTTP server for /feed and /health
sources/         — one poller per job board
```

## Current Status (verified 2026-04-14)

- [x] 502 resolved and `/health` returns `{"status": "ok"}`
- [x] `/feed` returns live JSON postings from the deployed service
- [x] Discord delivery path previously confirmed by user
- [ ] Wire `SCRAPER_FEED_URL=http://159.69.150.218` into NanoClaw tasks (see `nanoclaw/scraper/nanoclaw-tasks/`)
- [x] Task 16: Daily AI enrichment NanoClaw task registered
- [x] Task 17: Weekly newsletter NanoClaw task registered
- [x] Task 18: Weekly knowledge base update NanoClaw task registered
- [ ] Task 19: Extended end-to-end checks outside local pytest remain to be confirmed
- [ ] Task 20: Final config/docs pass

## Deployment (via ComputeEdge MCP in Claude Code)

```python
# Save credentials once
mcp__computeedge__set_credentials(provider="hetzner", token="<HETZNER_TOKEN>")
mcp__computeedge__set_credentials(key="DISCORD_WEBHOOK_URL", value="<WEBHOOK_URL>")
mcp__computeedge__set_credentials(key="DB_PATH", value="/data/postings.db")

# Deploy / redeploy
mcp__computeedge__deploy(
    provider_token="<HETZNER_TOKEN>",
    repo_path="https://github.com/Pabbsters/jojo-scraper",
    provider="hetzner"
)

# Monitor
mcp__computeedge__monitor(deployment_id="ce-hetzner-dbe06520")
```

## Full Plan

See `github.com/Pabbsters/nanoclaw` → `docs/superpowers/plans/2026-04-12-jojo-internship-alerts.md`
and `docs/superpowers/specs/2026-04-12-jojo-internship-alerts-design.md`
