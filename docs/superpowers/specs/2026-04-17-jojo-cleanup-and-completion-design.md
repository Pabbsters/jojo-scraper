# Jojo-Scraper Cleanup & Completion — Design

**Date**: 2026-04-17
**Author**: Ruthwik (brainstormed with Claude)
**Status**: Design approved, pending implementation plan

---

## Context

Jojo-scraper is functionally complete and deployed to Hetzner (`159.69.150.218:8080`). It polls 54 target companies via company-controlled ATS feeds (Greenhouse/Ashby/Lever/custom) and sends Discord alerts for matching seasonal postings.

Two categories of issues remain:

1. **Polling waste**: 10 quant firms are polled via Greenhouse/SmartRecruiters, but their feeds do not produce useful postings (they use their own apply-direct hiring systems). Polling them wastes cycles without ever alerting.
2. **Open deployment items** from the last session: NanoClaw scheduled tasks never re-registered after the DB was empty, and port 80 on the Hetzner firewall remains closed (forcing all URLs to include `:8080`).

This design covers both in one deploy.

## Goals

- Reclaim poll cycles wasted on quant firms that will never match.
- Keep quant firms visible as career targets (user still plans to apply direct).
- Re-register NanoClaw scheduled tasks so the enrichment pipeline resumes.
- Simplify URL hygiene by exposing the feed on port 80.

## Non-Goals

- Adding Meta / Microsoft / ByteDance direct scrapers. Aggregator repos (Simplify, Jobright, SpeedyApply) plus Jobright web UI provide adequate coverage. Revisit only if postings are observed to be missed in practice.
- Replacing quant firms with other targets. Career plan treats them as a separate apply-direct path; nothing needs substitution.
- Rewriting any source adapters.

## Design

### 1. Config surgery — remove quant firms from polling

**Keep** in `TIER1_COMPANIES` (they remain career targets): Jane Street, Hudson River Trading, IMC, Optiver, Jump Trading, DRW, Akuna Capital, Five Rings, Millennium, Point72.

**Remove** from:
- `GREENHOUSE_COMPANIES` — 9 entries: janestreet, hudsonrivertrading, imc, optiver, akunacapital, jumptrading, drw, fiverings, point72
- `TIER1_SOURCE_PREFERENCES` — 10 entries (the 9 above plus millennium, which uses SmartRecruiters)

**Mark** the quant entries in `TIER1_COMPANIES` with an inline comment group header: `# Apply-direct-only (no ATS polling)`.

Reason: scraper only polls via `*_COMPANIES` source lists; removal from those lists is sufficient to stop polling. Keeping entries in `TIER1_COMPANIES` preserves them for any consumer that inspects the full target universe.

### 2. Vault — update `top-companies.md` note

Current top-of-file note lists 4 apply-direct-only firms (Citadel, DE Shaw, Two Sigma, SIG). Expand to 14 by adding: Jane Street, HRT, IMC, Optiver, Jump Trading, DRW, Akuna, Five Rings, Millennium, Point72. Rewrite the reason: *"Now apply-direct-only because their ATS feeds don't expose useful seasonal/intern postings — polling was wasted cycles."*

### 3. Re-register NanoClaw scheduled tasks

Pre-checks:
- Locate `setup-tasks.sh` in the NanoClaw repo.
- Inspect the script to see what feed URL it uses. If hardcoded to `:8080`, leave it — works either way after Section 4. If it's a variable, update to drop the port after Section 4 is done.

Run `setup-tasks.sh`. Verify registration with `crontab -l` (or whatever scheduler the script uses — could be launchd, systemd timer, or cron).

### 4. Open port 80 via iptables NAT redirect

On `159.69.150.218` (as root):

```bash
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080
apt-get install -y iptables-persistent
netfilter-persistent save
```

Also confirm the Hetzner cloud firewall (separate layer from iptables) allows inbound TCP 80. If not, update via `hcloud firewall add-rule` or the Hetzner dashboard.

Verification: `curl http://159.69.150.218/health` from a machine outside the server must return `{"status":"ok"}`.

**Why iptables NAT over binding jojo to port 80 directly**: avoids granting the service `CAP_NET_BIND_SERVICE`, keeps the systemd unit unchanged, reversible with a single `iptables -t nat -D` line.

### 5. Dual-repo sync & deploy

Per CONTEXT.md, changes must be applied in both `~/jojo-scraper/` (deploy repo) and `~/nanoclaw/scraper/` on branch `feat/jojo-scraper` (source of truth).

Deploy sequence:
1. Apply config changes in both repos.
2. Commit in both; push both.
3. SSH to Hetzner: `cd /opt/jojo/app && git pull && systemctl restart jojo`.
4. Apply the iptables rule on the server (Section 4).
5. Update `top-companies.md` in Vault (Section 2).
6. Run NanoClaw `setup-tasks.sh` locally (Section 3).

### 6. Post-deploy verification

- `curl http://159.69.150.218/health` → `{"status":"ok"}`
- `curl http://159.69.150.218:8080/health` → still works (confirms NAT is an alias, not a move)
- `ssh root@159.69.150.218 "journalctl -u jojo --since '2 minutes ago'"` → no errors, no quant polls scheduled
- `crontab -l` (or equivalent) → NanoClaw tasks appear
- Update `CONTEXT.md`: tick the two open-item boxes, remove the port-80 caveat line

## Testing

No new code paths introduced; this is config + ops. Verification is end-to-end: health endpoint, log inspection, task registration. No unit tests required for this change set.

## Risks & Rollback

| Risk | Mitigation | Rollback |
|------|------------|----------|
| Quant firm removed from polling was actually producing a posting I cared about | Low likelihood — no alerts observed from them historically. | Revert the config commit, `systemctl restart jojo`. |
| iptables rule breaks inbound traffic | Test with `curl` from outside immediately; keep SSH session open during change. | `iptables -t nat -D PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080` |
| NanoClaw tasks fail to register (script moved/renamed) | Pre-check step locates script first. | If script missing, skip Section 3 and flag for manual follow-up. |
| `netfilter-persistent` not present on this Ubuntu image | `apt-get install -y iptables-persistent` creates it. | Fall back to systemd unit running `iptables-restore` at boot. |

## Open Questions

None — all 4 clarifying questions resolved before this design was written.
