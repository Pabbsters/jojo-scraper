# Jojo Scraper — Context for Codex

This is the standalone deploy repo for the jojo internship scraper. It is a copy of
`/nanoclaw/scraper/` on branch `feat/jojo-scraper` of `github.com/Pabbsters/nanoclaw`.

## Live Deployment

| Key | Value |
|-----|-------|
| URL | `http://178.104.199.240` |
| Health | `GET http://178.104.199.240/health` |
| Feed | `GET http://178.104.199.240/feed?since=<unix_ts>` |
| Provider | Hetzner (via ComputeEdge MCP) |
| Deployment ID | `ce-hetzner-44560faf` |
| Cost | $3.49/mo |

## Repos

| Repo | Purpose |
|------|---------|
| `github.com/Pabbsters/jojo-scraper` | **This repo** — what's deployed to Hetzner |
| `github.com/Pabbsters/nanoclaw` branch `feat/jojo-scraper` | Source of truth — also has docs + NanoClaw tasks |

When making changes, apply them here AND in `nanoclaw/scraper/` to keep them in sync.

## What This Does

Always-on Python scraper that:
- Polls 20+ job boards (Greenhouse, Ashby, Lever, GitHub, JobSpy, Amazon, Apple, Reddit, HN, Workday) every 15-60 min
- Matches postings against internship keywords for AI/Data, SWE, Cloud/Infra, MBB Consulting, Sales/Tech career tracks
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

## Remaining Tasks (as of 2026-04-14)

- [ ] Confirm 502 is resolved and `/health` returns `{"status": "ok"}`
- [ ] Verify Discord alert fires for a real posting
- [ ] Wire `SCRAPER_FEED_URL=http://178.104.199.240` into NanoClaw tasks (see `nanoclaw/scraper/nanoclaw-tasks/`)
- [ ] Task 16: Daily AI enrichment NanoClaw task (12 PM + 6 PM CST)
- [ ] Task 17: Weekly newsletter NanoClaw task (Sunday 3 PM CST)
- [ ] Task 18: Weekly knowledge base update NanoClaw task (Saturday 2 AM CST)
- [ ] Task 19: Integration tests pass end-to-end

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
mcp__computeedge__monitor(deployment_id="ce-hetzner-44560faf")
```

## Full Plan

See `github.com/Pabbsters/nanoclaw` → `docs/superpowers/plans/2026-04-12-jojo-internship-alerts.md`
and `docs/superpowers/specs/2026-04-12-jojo-internship-alerts-design.md`
