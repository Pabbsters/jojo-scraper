# Jojo-Scraper Cleanup & Completion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove 10 quant firms from polling (keep as targets), re-register NanoClaw scheduled tasks, open port 80 on Hetzner via iptables NAT redirect.

**Architecture:** Config-only change to `config.py` — remove quant slugs from `GREENHOUSE_COMPANIES` and `TIER1_SOURCE_PREFERENCES`. Keep them in `TIER1_COMPANIES`. Mirror changes in the dual source-of-truth repo (`~/nanoclaw/scraper/`). Deploy via `git pull` + `systemctl restart jojo`. Layer-3 fix for port 80 (iptables NAT) to avoid service reconfiguration. NanoClaw tasks re-registered by re-running existing `setup-tasks.sh`.

**Tech Stack:** Python 3.12, pytest, Ubuntu 24.04 (Hetzner), iptables, systemd, macOS launchd (NanoClaw side).

**Spec:** `docs/superpowers/specs/2026-04-17-jojo-cleanup-and-completion-design.md`

---

## Quant firms to remove (reference list — used by multiple tasks)

| Slug | Name | Source | Lists to remove from |
|---|---|---|---|
| `janestreet` | Jane Street | greenhouse | `GREENHOUSE_COMPANIES`, `TIER1_SOURCE_PREFERENCES` |
| `hudsonrivertrading` | Hudson River Trading | greenhouse (board_slug=wehrtyou) | `GREENHOUSE_COMPANIES`, `TIER1_SOURCE_PREFERENCES` |
| `imc` | IMC | greenhouse | `GREENHOUSE_COMPANIES`, `TIER1_SOURCE_PREFERENCES` |
| `optiver` | Optiver | greenhouse | `GREENHOUSE_COMPANIES`, `TIER1_SOURCE_PREFERENCES` |
| `akunacapital` | Akuna Capital | greenhouse | `GREENHOUSE_COMPANIES`, `TIER1_SOURCE_PREFERENCES` |
| `jumptrading` | Jump Trading | greenhouse | `GREENHOUSE_COMPANIES`, `TIER1_SOURCE_PREFERENCES` |
| `drw` | DRW | greenhouse (board_slug=drweng) | `GREENHOUSE_COMPANIES`, `TIER1_SOURCE_PREFERENCES` |
| `fiverings` | Five Rings | greenhouse (board_slug=fiveringsllc) | `GREENHOUSE_COMPANIES`, `TIER1_SOURCE_PREFERENCES` |
| `point72` | Point72 | greenhouse | `GREENHOUSE_COMPANIES`, `TIER1_SOURCE_PREFERENCES` |
| `millennium` | Millennium | smartrecruiters | `TIER1_SOURCE_PREFERENCES` only |

All 10 stay in `TIER1_COMPANIES`.

---

## Task 1: Write failing tests for quant exclusion

**Files:**
- Modify: `/Users/ruthwikpabbu/jojo-scraper/tests/test_config_registry.py`

- [ ] **Step 1: Add failing test that quant slugs are absent from polling sources**

Append to the end of `tests/test_config_registry.py`:

```python
QUANT_SLUGS_NOT_POLLED = {
    "janestreet",
    "hudsonrivertrading",
    "imc",
    "optiver",
    "akunacapital",
    "jumptrading",
    "drw",
    "fiverings",
    "point72",
    "millennium",
}


def test_quant_firms_stay_in_tier1_registry() -> None:
    registry = {company["slug"] for company in TIER1_COMPANIES}
    for slug in QUANT_SLUGS_NOT_POLLED:
        assert slug in registry, (
            f"{slug} must remain a career target even though it's no longer polled"
        )


def test_quant_firms_are_not_in_greenhouse_companies() -> None:
    greenhouse_slugs = {company["slug"] for company in GREENHOUSE_COMPANIES}
    leaked = QUANT_SLUGS_NOT_POLLED & greenhouse_slugs
    assert leaked == set(), f"Quant firms still polled via Greenhouse: {leaked}"


def test_quant_firms_are_not_in_tier1_source_preferences() -> None:
    leaked = QUANT_SLUGS_NOT_POLLED & set(TIER1_SOURCE_PREFERENCES.keys())
    assert leaked == set(), f"Quant firms still in TIER1_SOURCE_PREFERENCES: {leaked}"
```

- [ ] **Step 2: Run the new tests — expect FAIL**

```bash
cd /Users/ruthwikpabbu/jojo-scraper
python3 -m pytest tests/test_config_registry.py -v -k quant
```

Expected output: 2 FAIL (the "not in" tests), 1 PASS (`test_quant_firms_stay_in_tier1_registry`). The failures are what we want — they prove the tests detect the current broken state.

- [ ] **Step 3: Commit the failing tests**

```bash
cd /Users/ruthwikpabbu/jojo-scraper
git add tests/test_config_registry.py
git commit -m "test: add quant-firm polling-exclusion assertions (failing)"
```

---

## Task 2: Remove quant entries from `GREENHOUSE_COMPANIES`

**Files:**
- Modify: `/Users/ruthwikpabbu/jojo-scraper/config.py`

- [ ] **Step 1: Delete the 9 quant entries from `GREENHOUSE_COMPANIES`**

Open `config.py` and locate the `GREENHOUSE_COMPANIES: list[dict[str, str]] = [` block (currently starts near line 207). Delete these 9 lines exactly:

```python
    {"slug": "imc", "name": "IMC"},
    {"slug": "optiver", "name": "Optiver"},
    {"slug": "akunacapital", "name": "Akuna Capital"},
    {"slug": "jumptrading", "name": "Jump Trading"},
    {"slug": "drw", "name": "DRW", "board_slug": "drweng"},
    {"slug": "fiverings", "name": "Five Rings", "board_slug": "fiveringsllc"},
    {"slug": "point72", "name": "Point72"},
    {"slug": "janestreet", "name": "Jane Street"},
    {"slug": "hudsonrivertrading", "name": "Hudson River Trading", "board_slug": "wehrtyou"},
```

Use Edit tool with exact `old_string` matches for each line (or one multi-line Edit if they're contiguous). Verify by re-reading the block — only non-quant entries should remain.

- [ ] **Step 2: Run the Greenhouse test — expect PASS**

```bash
cd /Users/ruthwikpabbu/jojo-scraper
python3 -m pytest tests/test_config_registry.py::test_quant_firms_are_not_in_greenhouse_companies -v
```

Expected: PASS.

- [ ] **Step 3: Do NOT commit yet — continue to Task 3**

---

## Task 3: Remove quant entries from `TIER1_SOURCE_PREFERENCES`

**Files:**
- Modify: `/Users/ruthwikpabbu/jojo-scraper/config.py`

- [ ] **Step 1: Delete the 10 quant entries from `TIER1_SOURCE_PREFERENCES`**

Locate the `TIER1_SOURCE_PREFERENCES: dict[str, dict[str, str]] = {` block (currently near line 152). Delete these 10 lines:

```python
    "janestreet": {"preferred_source": "greenhouse", "source_type": "direct"},
    "hudsonrivertrading": {"preferred_source": "greenhouse", "source_type": "direct"},
    "imc": {"preferred_source": "greenhouse", "source_type": "direct"},
    "optiver": {"preferred_source": "greenhouse", "source_type": "direct"},
    "akunacapital": {"preferred_source": "greenhouse", "source_type": "direct"},
    "jumptrading": {"preferred_source": "greenhouse", "source_type": "direct"},
    "drw": {"preferred_source": "greenhouse", "source_type": "direct"},
    "fiverings": {"preferred_source": "greenhouse", "source_type": "direct"},
    "point72": {"preferred_source": "greenhouse", "source_type": "direct"},
    "millennium": {"preferred_source": "smartrecruiters", "source_type": "direct"},
```

- [ ] **Step 2: Add a header comment block above `TIER1_COMPANIES`**

The quant slugs are scattered throughout `TIER1_COMPANIES` (not grouped), so per-entry comments would be noisy. Add a single block comment immediately above the `TIER1_COMPANIES: list[dict[str, str]] = [` line (near line 91). Use Edit tool to replace the existing `# ── Curated top-60 company list ────────────────────────────────────────` header comment block with:

```python
# ── Curated top-60 company list ────────────────────────────────────────
# This registry mirrors ``top-companies.md`` exactly. Companies only receive a
# direct-source preference once we have a live, working careers endpoint.
#
# NOTE: 10 quant firms are listed here as career targets but are NOT polled
# (their ATS feeds don't expose useful postings). See top-companies.md for
# the apply-direct-only list: Jane Street, HRT, IMC, Optiver, Jump Trading,
# DRW, Akuna, Five Rings, Millennium, Point72.
```

This replaces lines 88-90 (the current 3-line header). Do NOT reorder the company entries themselves.

- [ ] **Step 3: Run all config registry tests — expect PASS**

```bash
cd /Users/ruthwikpabbu/jojo-scraper
python3 -m pytest tests/test_config_registry.py -v
```

Expected: ALL PASS, including the 3 new quant assertions. If `test_hidden_board_slug_overrides_are_present_for_verified_boards` fails on `hudsonrivertrading`, `drw`, or `fiverings`, proceed to Task 4 to fix it.

- [ ] **Step 4: Do NOT commit yet — continue to Task 4**

---

## Task 4: Fix stale `test_hidden_board_slug_overrides` assertions

**Files:**
- Modify: `/Users/ruthwikpabbu/jojo-scraper/tests/test_config_registry.py`

This test currently asserts `greenhouse_overrides["hudsonrivertrading"] == "wehrtyou"`, `greenhouse_overrides["drw"] == "drweng"`, `greenhouse_overrides["fiverings"] == "fiveringsllc"`. Since those entries are now deleted, the dict lookups will raise `KeyError`.

- [ ] **Step 1: Remove the 3 dead assertions**

In `tests/test_config_registry.py`, locate the `test_hidden_board_slug_overrides_are_present_for_verified_boards` function and delete these 3 lines:

```python
    assert greenhouse_overrides["hudsonrivertrading"] == "wehrtyou"
    assert greenhouse_overrides["drw"] == "drweng"
    assert greenhouse_overrides["fiverings"] == "fiveringsllc"
```

Keep the `scaleai` and `dbtlabsinc` assertions — those companies are still polled.

- [ ] **Step 2: Run the full test file — expect ALL PASS**

```bash
cd /Users/ruthwikpabbu/jojo-scraper
python3 -m pytest tests/test_config_registry.py -v
```

Expected: all tests pass.

- [ ] **Step 3: Run the full test suite — expect ALL PASS**

```bash
cd /Users/ruthwikpabbu/jojo-scraper
python3 -m pytest -x
```

Expected: no regressions. If any test fails, investigate before proceeding. The `-x` flag stops at the first failure so you can fix it.

- [ ] **Step 4: Commit the config + test changes**

```bash
cd /Users/ruthwikpabbu/jojo-scraper
git add config.py tests/test_config_registry.py
git commit -m "feat: stop polling quant firms, keep them as career targets"
```

---

## Task 5: Mirror changes in `nanoclaw/scraper/`

Per `CONTEXT.md`, changes must be applied to both `jojo-scraper` (deploy repo) AND `nanoclaw/scraper/` (source of truth) to keep them in sync.

**Files:**
- Modify: `/Users/ruthwikpabbu/nanoclaw/scraper/config.py`
- Modify: `/Users/ruthwikpabbu/nanoclaw/scraper/tests/test_config_registry.py`

- [ ] **Step 1: Copy the updated files from jojo-scraper**

```bash
cp /Users/ruthwikpabbu/jojo-scraper/config.py /Users/ruthwikpabbu/nanoclaw/scraper/config.py
cp /Users/ruthwikpabbu/jojo-scraper/tests/test_config_registry.py /Users/ruthwikpabbu/nanoclaw/scraper/tests/test_config_registry.py
```

- [ ] **Step 2: Run the tests in the nanoclaw copy — expect PASS**

```bash
cd /Users/ruthwikpabbu/nanoclaw/scraper
python3 -m pytest tests/test_config_registry.py -v
```

Expected: all pass.

- [ ] **Step 3: Commit to nanoclaw on branch `feat/jojo-scraper`**

```bash
cd /Users/ruthwikpabbu/nanoclaw
git checkout feat/jojo-scraper
git add scraper/config.py scraper/tests/test_config_registry.py
git commit -m "feat(scraper): stop polling quant firms, keep as career targets"
```

If you aren't on `feat/jojo-scraper`, `git checkout` will switch. If there are unrelated changes in the working tree, stash them first: `git stash push -m 'pre-quant-change'`.

---

## Task 6: Push both repos

- [ ] **Step 1: Push jojo-scraper**

```bash
cd /Users/ruthwikpabbu/jojo-scraper
git push origin main
```

Expected: push succeeds. If rejected due to remote-ahead, pull-rebase first: `git pull --rebase origin main`.

- [ ] **Step 2: Push nanoclaw**

```bash
cd /Users/ruthwikpabbu/nanoclaw
git push origin feat/jojo-scraper
```

Expected: push succeeds.

---

## Task 7: Deploy to Hetzner

- [ ] **Step 1: SSH to Hetzner and pull latest**

```bash
ssh root@159.69.150.218 "cd /opt/jojo/app && git pull && systemctl restart jojo"
```

Expected: `Fast-forward` output from git pull, no errors from systemctl.

- [ ] **Step 2: Verify service is healthy**

```bash
ssh root@159.69.150.218 "systemctl is-active jojo"
```

Expected: `active`

```bash
curl http://159.69.150.218:8080/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 3: Confirm quant firms no longer polled in logs**

```bash
ssh root@159.69.150.218 "journalctl -u jojo --since '3 minutes ago' --no-pager | grep -iE 'janestreet|hudsonrivertrading|optiver|jumptrading|drw|akuna|fiverings|point72|imc|millennium' | head -20"
```

Expected: **no output** (grep returns nothing). If any quant slug appears in a poll log line, the deploy didn't pick up the new config — re-check Step 1.

---

## Task 8: Open port 80 via iptables NAT redirect

- [ ] **Step 1: Verify Hetzner cloud firewall permits inbound port 80**

From your Mac:
```bash
hcloud firewall list 2>/dev/null || echo "hcloud CLI not installed — check dashboard at https://console.hetzner.cloud"
```

If `hcloud` is installed, find the firewall attached to server `127007627`:
```bash
hcloud server describe 127007627 | grep -A 5 -i firewall
hcloud firewall describe <firewall-id>
```

If there's no firewall attached to the server, or the firewall already permits TCP 80 inbound (`0.0.0.0/0`), proceed to Step 2. If TCP 80 is blocked, add a rule:
```bash
hcloud firewall add-rule <firewall-id> --direction in --protocol tcp --port 80 --source-ips 0.0.0.0/0 --source-ips ::/0
```

If `hcloud` is not installed and you aren't sure of firewall state: open the Hetzner Cloud console → server 127007627 → Networking → confirm inbound rules include TCP 80. Add if missing.

- [ ] **Step 2: Add iptables NAT redirect on the server**

```bash
ssh root@159.69.150.218 "iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080"
```

Expected: no output, exit code 0.

- [ ] **Step 3: Verify the rule is in place**

```bash
ssh root@159.69.150.218 "iptables -t nat -L PREROUTING -n --line-numbers | grep 'dpt:80'"
```

Expected: a line similar to `REDIRECT tcp -- 0.0.0.0/0 0.0.0.0/0 tcp dpt:80 redir ports 8080`.

- [ ] **Step 4: Test port 80 reaches `/health`**

From your Mac:
```bash
curl -sS http://159.69.150.218/health
```

Expected: `{"status":"ok"}`. If it hangs or returns an error, the Hetzner firewall is blocking port 80 — return to Step 1.

Also confirm port 8080 still works (NAT is an alias, not a move):
```bash
curl -sS http://159.69.150.218:8080/health
```

Expected: `{"status":"ok"}`.

- [ ] **Step 5: Persist the rule across reboots**

```bash
ssh root@159.69.150.218 "DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent && netfilter-persistent save"
```

Expected: installs package (if not already present) and saves current rules to `/etc/iptables/rules.v4`. `iptables-persistent` on Ubuntu 24.04 asks via debconf during install whether to save current rules; `DEBIAN_FRONTEND=noninteractive` + the explicit `netfilter-persistent save` covers both paths.

- [ ] **Step 6: Verify persistence**

```bash
ssh root@159.69.150.218 "grep -E 'dport 80|--dport 80' /etc/iptables/rules.v4"
```

Expected: a line containing the NAT redirect rule. If empty, run `netfilter-persistent save` again.

---

## Task 9: Re-register NanoClaw scheduled tasks

**Files:**
- Run: `/Users/ruthwikpabbu/nanoclaw/scraper/nanoclaw-tasks/setup-tasks.sh`

- [ ] **Step 1: Inspect the script to confirm it's runnable**

```bash
cat /Users/ruthwikpabbu/nanoclaw/scraper/nanoclaw-tasks/setup-tasks.sh | head -40
```

Expected: `#!/bin/bash`, sets `SCRAPER_URL`, creates `IPC_DIR`. Confirm the script references an `$IPC_DIR` that exists:

```bash
ls -la /Users/ruthwikpabbu/nanoclaw/data/ipc/discord_main/tasks/ 2>/dev/null || echo "(dir doesn't exist — script will mkdir -p)"
```

Either result is fine (the script creates the dir).

- [ ] **Step 2: Run the setup script**

```bash
bash /Users/ruthwikpabbu/nanoclaw/scraper/nanoclaw-tasks/setup-tasks.sh
```

Expected: script completes with exit code 0. Any output is informational.

- [ ] **Step 3: Verify tasks are registered**

The script writes task files into `$IPC_DIR`. Verify:

```bash
ls -la /Users/ruthwikpabbu/nanoclaw/data/ipc/discord_main/tasks/
```

Expected: one or more task JSON files present. If empty, inspect the script for errors by running with `bash -x` and investigate.

- [ ] **Step 4: (Optional) Sanity-check the enrichment pre-check works against the feed**

```bash
curl -sf "http://159.69.150.218:8080/feed?since=$(python3 -c 'import time; print(int(time.time()-43200))')" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'postings in last 12h: {len(d.get(\"postings\",[]))}')"
```

Expected: a number (likely `0` if no seasonal posting has matched yet — that's fine). The check confirms the feed endpoint is reachable from NanoClaw's perspective.

---

## Task 10: Update Vault `top-companies.md`

**Files:**
- Modify: `/Users/ruthwikpabbu/Vault/NanoClaw/career-plan/top-companies.md`

- [ ] **Step 1: Update the top-of-file note**

Replace the current note (starts with `> **Note on jojo-scraper coverage**`) with:

```markdown
> **Note on jojo-scraper coverage**: jojo tracks the 58 companies below as career targets. 14 of them are **apply-direct-only** (not polled by jojo) — apply directly at their career pages:
>
> **Quant / HFT (10):** Jane Street, Hudson River Trading, IMC, Optiver, Jump Trading, DRW, Akuna Capital, Five Rings, Millennium, Point72
> **Also apply-direct (4):** Citadel / Citadel Securities, DE Shaw, Two Sigma, SIG (Susquehanna)
>
> Reason: their ATS feeds (Greenhouse/SmartRecruiters) don't expose useful seasonal/intern postings the way Anthropic, Stripe, or Databricks do — polling them was wasted cycles. They remain strong Tier S/4 targets if you pursue `/Quant_Analyst`.
```

Also update the `**Last updated**:` line at the top of the file to today's date.

- [ ] **Step 2: Verify the change looks right**

```bash
head -15 /Users/ruthwikpabbu/Vault/NanoClaw/career-plan/top-companies.md
```

Expected: the new note appears; date is current.

No git commit — Vault is not under git per user's setup. (If Vault becomes git-managed later, add a commit step.)

---

## Task 11: Update `CONTEXT.md` (both repos)

**Files:**
- Modify: `/Users/ruthwikpabbu/jojo-scraper/CONTEXT.md`
- Modify: `/Users/ruthwikpabbu/nanoclaw/scraper/CONTEXT.md` (if it exists — check first)

- [ ] **Step 1: Update `Current Status` section in jojo-scraper CONTEXT.md**

In `/Users/ruthwikpabbu/jojo-scraper/CONTEXT.md`, change:

```markdown
- [ ] NanoClaw scheduled tasks not yet re-registered (DB was empty); re-run setup-tasks.sh once NanoClaw is running
- [ ] Port 80 not open — all NanoClaw URLs must use :8080
```

To:

```markdown
- [x] NanoClaw scheduled tasks re-registered (2026-04-18)
- [x] Port 80 open via iptables NAT redirect (2026-04-18); URLs may omit :8080
```

Also update the `## Current Status (verified YYYY-MM-DD)` line to today's date.

- [ ] **Step 2: Sync to nanoclaw if a CONTEXT.md exists there**

```bash
test -f /Users/ruthwikpabbu/nanoclaw/scraper/CONTEXT.md && cp /Users/ruthwikpabbu/jojo-scraper/CONTEXT.md /Users/ruthwikpabbu/nanoclaw/scraper/CONTEXT.md || echo "no CONTEXT.md in nanoclaw/scraper — skipping"
```

- [ ] **Step 3: Commit CONTEXT.md updates in both repos**

```bash
cd /Users/ruthwikpabbu/jojo-scraper
git add CONTEXT.md
git commit -m "docs: mark NanoClaw tasks + port 80 as done"
git push origin main

cd /Users/ruthwikpabbu/nanoclaw
if git diff --quiet scraper/CONTEXT.md; then
  echo "no CONTEXT.md changes in nanoclaw"
else
  git add scraper/CONTEXT.md
  git commit -m "docs(scraper): mark NanoClaw tasks + port 80 as done"
  git push origin feat/jojo-scraper
fi
```

---

## Task 12: Final end-to-end verification

- [ ] **Step 1: Health check from fresh shell**

```bash
curl -sS http://159.69.150.218/health && echo && curl -sS http://159.69.150.218:8080/health
```

Expected: `{"status":"ok"}` twice.

- [ ] **Step 2: Confirm jojo service picked up new config**

```bash
ssh root@159.69.150.218 "systemctl status jojo --no-pager | head -20"
```

Expected: `active (running)`, recent restart timestamp matches your deploy time.

- [ ] **Step 3: Confirm no quant activity for 5 minutes**

```bash
ssh root@159.69.150.218 "journalctl -u jojo --since '5 minutes ago' --no-pager | grep -cE 'janestreet|hudsonrivertrading|optiver|jumptrading|drw|akuna|fiverings|point72|imc|millennium'"
```

Expected: `0`. If non-zero, grep those lines to investigate: the config may not have reloaded.

- [ ] **Step 4: Confirm NanoClaw tasks are registered**

```bash
ls /Users/ruthwikpabbu/nanoclaw/data/ipc/discord_main/tasks/
```

Expected: one or more task files.

- [ ] **Step 5: Final summary**

Report back to user:
- All 10 quant firms removed from polling, still in `TIER1_COMPANIES` as targets
- Port 80 reachable: `curl http://159.69.150.218/health` → `ok`
- NanoClaw tasks re-registered
- CONTEXT.md updated in both repos

---

## Rollback Quick Reference

If anything goes wrong and you need to revert:

**Config changes:**
```bash
cd /Users/ruthwikpabbu/jojo-scraper && git revert HEAD~1 && git push
cd /Users/ruthwikpabbu/nanoclaw && git revert HEAD~1 && git push
ssh root@159.69.150.218 "cd /opt/jojo/app && git pull && systemctl restart jojo"
```

**iptables rule:**
```bash
ssh root@159.69.150.218 "iptables -t nat -D PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080 && netfilter-persistent save"
```

**NanoClaw tasks:**
```bash
rm -f /Users/ruthwikpabbu/nanoclaw/data/ipc/discord_main/tasks/*
```
