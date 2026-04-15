# Jojo Scraper — Codex Handoff Prompt

## Context

You are picking up the jojo internship scraper project for Ruthwik Pabbu (Stats + CS + DS, UIUC).
The scraper is fully deployed and live. Full context is at:
- `github.com/Pabbsters/jojo-scraper` — deployed code, CONTEXT.md, docs/PLAN.md, docs/DESIGN.md
- `github.com/Pabbsters/nanoclaw` branch `feat/jojo-scraper` — source of truth

**Live deployment:** `http://159.69.150.218` (Hetzner via ComputeEdge MCP, $3.49/mo)
**Deployment ID:** `ce-hetzner-815715f4`

Read `CONTEXT.md` and `docs/PLAN.md` before starting. The PLAN.md has the full task list.

---

## What's Already Done

- [x] Scraper polls Greenhouse, Ashby, Lever, GitHub, JobSpy (Indeed/LinkedIn/Google/ZipRecruiter), Amazon, Apple, Reddit, HN, Workday
- [x] SQLite dedup, Discord webhook alerts (Format B rich card), /feed + /health HTTP endpoints
- [x] Deployed to Hetzner via ComputeEdge MCP — `/health` returns 200, `/feed` returns real postings
- [x] NanoClaw scheduled tasks registered: daily enrichment (12PM+6PM CST), weekly newsletter (Sun 3PM CST), weekly KB update (Sat 2AM CST)
- [x] SCRAPER_FEED_URL wired into all NanoClaw task scripts pointing at `http://159.69.150.218`
- [x] Bachelor's-level filter added — rejects PhD, senior, staff, principal, director roles and requires intern/new-grad/entry-level signal in title
- [x] 184/184 tests passing

---

## Your Tasks (in priority order)

### 1. Redeploy with latest code (REQUIRED FIRST)

Several fixes were committed after the last deploy. Redeploy so the live server has the bachelor's filter and all bug fixes:

```python
# Via ComputeEdge MCP
mcp__computeedge__deploy(
    provider_token="<HETZNER_TOKEN>",  # ask Ruthwik
    repo_path="https://github.com/Pabbsters/jojo-scraper",
    provider="hetzner",
    force_new=False
)
```

After deploy, verify:
```bash
curl http://159.69.150.218/health          # → {"status": "ok"}
curl "http://159.69.150.218/feed" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['postings']), 'postings')"
```

### 2. Confirm Discord alerts landed

Check Discord guild `1492621390518681932` (Ruthwik's server). The scraper sent alerts for 14 postings during the first poll. You should see rich-card embeds from the webhook. If no alerts appear:

- Check `discord_alert.py` — the webhook URL is injected as `DISCORD_WEBHOOK_URL` env var via ComputeEdge
- Verify the env var is set: it's saved in ComputeEdge config as `DISCORD_WEBHOOK_URL`
- If needed, trigger a test alert by hitting the scraper endpoint and checking if new postings flow through

### 3. Run full integration tests

```bash
cd /path/to/jojo-scraper
pip install -r requirements.txt
python -m pytest tests/ -v --tb=short
```

Expected: 184 passed. Fix any failures — do NOT skip or mock.

### 4. Stability check (1 hour)

After confirming the deploy is live:

```python
mcp__computeedge__monitor(deployment_id="ce-hetzner-815715f4")
```

Check:
- RAM usage stays under 80% (3819MB total — plenty of headroom)
- CPU doesn't spike and stay high
- Hit `/feed` every 15 min for an hour and confirm postings accumulate

### 5. Fix test coverage for bachelor's filter (new code, no tests yet)

`matching.py` was updated to add `_is_bachelor_level()` filtering. The existing `tests/test_matching.py` doesn't cover the new filter. Add tests for:

- PhD posting → returns None
- Senior engineer posting → returns None  
- Intern posting matching a track → returns match
- New grad posting → returns match
- Posting with no intern signal in title → returns None
- Posting with intern signal but PhD in description → returns None

### 6. Wire up NanoClaw enrichment task (if not auto-picked up)

The `setup-tasks.sh` was already run. Check if NanoClaw picked up the tasks:

```bash
sqlite3 ~/nanoclaw/store/messages.db 'SELECT id, status, next_run FROM scheduled_tasks WHERE id LIKE "jojo-%"'
```

If the tasks aren't registered, re-run:
```bash
SCRAPER_URL=http://159.69.150.218 bash ~/nanoclaw/scraper/nanoclaw-tasks/setup-tasks.sh
```

### 7. Config tuning based on rate limits

After the first few poll cycles, some sources may rate-limit. Check logs and:
- Increase intervals for rate-limited sources in `config.py` under `POLL_INTERVAL_MINUTES`
- Note: this key is read by `main.py` but may not exist yet in `config.py` — add it if missing

### 8. Final commit and PR

Once everything is verified:
1. Commit all changes to `feat/jojo-scraper` in `github.com/Pabbsters/nanoclaw`
2. Sync changes to `github.com/Pabbsters/jojo-scraper` (keep both in sync)
3. Open a PR from `feat/jojo-scraper` → `main` in Pabbsters/nanoclaw

---

## Key Files

| File | What it does |
|------|-------------|
| `main.py` | Async entry point, APScheduler, initial poll |
| `matching.py` | **Bachelor's filter + track classifier** — recently updated |
| `config.py` | `INTERN_TITLE_PATTERNS`, `EXCLUDE_PATTERNS`, company lists, keywords |
| `db.py` | SQLite with `check_same_thread=False` (required for feed thread) |
| `feed.py` | HTTP server — reads `PORT` from env (ComputeEdge injects 3000) |
| `discord_alert.py` | Webhook sender |
| `sources/` | One file per job board |
| `nanoclaw-tasks/setup-tasks.sh` | Registers 3 NanoClaw scheduled tasks |
| `tests/` | pytest suite — 184 tests |

---

## Known Issues / Watch Out For

- ComputeEdge creates a **new VM on every deploy** — always use `force_new=False` and destroy old ones after confirming the new one works, or you'll hit the Hetzner server limit
- `check_same_thread=False` in `db.py` is intentional — SQLite is accessed from both the main asyncio thread and the feed server thread
- `DB_PATH=/app/postings.db` (not `/data/`) — no volume mount in ComputeEdge
- LinkedIn scraping uses `linkedin_fetch_description=False` — no Playwright needed, titles/companies work fine
- Glassdoor is excluded (requires Playwright/Chromium which bloats the image)

---

## Ruthwik's Career Tracks (for filter tuning)

Priority order for alerts:
1. **ai_data** — AI engineer, ML, data science, research
2. **swe** — Software engineer, full stack, mobile
3. **sales_technical** — Solutions architect, developer advocate
4. **consulting** — MBB + Big 4
5. **extras** — Quant, fintech, robotics, web3
6. **cloud_infra** — Cloud, SRE, cybersecurity, DevOps

Target companies include: Anthropic, OpenAI, Cohere, Databricks, Citadel, Jane Street, Palantir, Cloudflare, Netflix, SpaceX, Scale AI, and all FANG.
