# Jojo Scraper — Context for Codex

This is the standalone deploy repo for the jojo internship scraper. It is a copy of
`/nanoclaw/scraper/` on branch `feat/jojo-scraper` of `github.com/Pabbsters/nanoclaw`.

## Live Deployment

| Key | Value |
|-----|-------|
| URL | `http://159.69.150.218:8080` |
| Health | `GET http://159.69.150.218:8080/health` |
| Feed | `GET http://159.69.150.218:8080/feed?since=<unix_ts>` |
| Provider | Hetzner (CX23, server ID 127007627) |
| Deployment | systemd + venv, Ubuntu 24.04 |
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

- [x] `/health` returns `{"status": "ok"}` at port 8080
- [x] `/feed` responds live — 0 postings until a matching fresh seasonal posting arrives
- [x] Discord webhook verified — test embed delivered 2026-04-16
- [x] DISCORD_WEBHOOK_URL injected via `/opt/jojo/.env` on server
- [x] NanoClaw task scripts updated to use port 8080
- [x] Enrichment prompt updated for direct-only top-50 seasonal policy
- [ ] NanoClaw scheduled tasks not yet re-registered (DB was empty); re-run setup-tasks.sh once NanoClaw is running
- [ ] Port 80 not open — all NanoClaw URLs must use :8080

## Deployment (Hetzner API + cloud-init)

Server ID: `127007627`, IP: `159.69.150.218`, type: CX23, Ubuntu 24.04

SSH access: `ssh root@159.69.150.218` (uses `~/.ssh/id_ed25519`)

Service management:
```bash
ssh root@159.69.150.218 "systemctl status jojo"
ssh root@159.69.150.218 "journalctl -u jojo -f"
ssh root@159.69.150.218 "systemctl restart jojo"
```

To redeploy latest code:
```bash
ssh root@159.69.150.218 "cd /opt/jojo/app && git pull && systemctl restart jojo"
```

Credentials stored in `~/.config/jojo/secrets.env` (never commit).

## Full Plan

See `github.com/Pabbsters/nanoclaw` → `docs/superpowers/plans/2026-04-12-jojo-internship-alerts.md`
and `docs/superpowers/specs/2026-04-12-jojo-internship-alerts-design.md`
