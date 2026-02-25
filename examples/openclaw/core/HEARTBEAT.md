# HEARTBEAT.md
# OpenClaw Heartbeat Protocol — AI SAFE² Engage & Monitor Standard

**Load context:** Every session if heartbeats are enabled. During heartbeat turns, this file governs all behavior.  
**Governed by:** AI SAFE² Framework · Dual License MIT + CC-BY-SA  
**AI SAFE² Pillar:** E — Engage & Monitor

---

## 1. What a Heartbeat Is

A heartbeat is a **scheduled, autonomous health check** the agent runs periodically (typically every 30–60 minutes) to verify system integrity, sync state, and catch failures the user would otherwise miss. It is not a conversation turn. It is a maintenance run.

**Default output:** `NO_REPLY` — the heartbeat completes silently unless it finds something requiring user attention. A heartbeat that messages the user on every run defeats the purpose (notification fatigue is itself a security risk — it trains users to ignore alerts).

**Exception:** Send a direct message when the notifier path itself is broken and the user needs to intervene, or when a critical-priority finding requires immediate action.

---

## 2. Every Heartbeat

Run these checks on every heartbeat cycle:

### 2.1 State File Integrity

```json
// Expected structure of memory/heartbeat-state.json
{
  "lastChecks": {
    "errorLog": null,
    "securityAudit": null,
    "lastDailyChecks": null,
    "weeklyGatewayVerify": null
  }
}
```

If `heartbeat-state.json` is missing or corrupted, replace with the default above and alert the user once.

Update timestamps for every check performed during this run.

### 2.2 Git Backup / Workspace Sync

- Run the auto-git-sync script.
- If it exits non-zero: log a warning in heartbeat state, continue other checks.
- Alert the user only for real breakages (merge conflicts, persistent push failures after retry).
- Routine "nothing to commit" exits are silent.

### 2.3 Gateway Usage Sync

- Sync LLM API calls from session transcripts into the interaction store.
- All model usage must be centrally tracked for cost control and audit.
- If the interaction store is unreachable, log and alert.

### 2.4 System Health Check

- Run the health check script with `--notify`.
- The script handles one-time failure/recovery delivery — do not duplicate notifications.
- Log all check results to heartbeat-state.json.

### 2.5 Cron Failure Deltas

- Check for new cron failures since the last heartbeat.
- Use `--notify` so the notifier handles delivery priority and deduplication.
- Only new failures (delta, not total) are reported. A persistent known failure is reported once until resolved.

### 2.6 Persistent Failure Check

- Scan for failures that have recurred across multiple heartbeats.
- Escalate persistent failures to the user regardless of priority tier — a repeated failure indicates a systemic issue.

### 2.7 AI SAFE² Security Scan (Quick)

Run the AI SAFE² scanner in quick mode:

```bash
python3 scanner.py --target ./openclaw-data --quick
```

Flag and alert on any finding that scores 8.0+ (Critical) or represents a new finding since last scan:
- API keys or secrets found in logs or config files
- World-readable credential files
- Admin panel bound to `0.0.0.0` instead of `127.0.0.1`
- Gateway token missing or empty
- New dangerous tool enabled (exec, browser) without recorded approval

---

## 3. Once Daily

Run these additional checks once per day (use `lastDailyChecks` timestamp to gate):

### 3.1 Data Collection Health

- Check all data ingestion pipelines for silent failures.
- Use `--notify` for delivery.

### 3.2 Repository Size Check

- Alert if git repo exceeds size threshold (default: 500MB).
- Large repos indicate log files or binary data accidentally committed.

### 3.3 Memory Index Coverage

- Alert if memory index coverage drops below 80%.
- Low coverage means `memory_search` will miss relevant results — this silently degrades agent usefulness.

### 3.4 Memory Synthesis Opportunity

- If daily notes have accumulated > 5 entries not yet reflected in MEMORY.md, draft a proposed MEMORY.md update and surface it to the user.
- Do not auto-merge. Draft only.

### 3.5 Love Equation Alignment Check

Tally the session's C (cooperation) and D (defection) events from today's memory log. Report if:
- D events exceeded 0 (any defection in a session is notable)
- The running C/D ratio has declined over the past 3 days (drift indicator)
- Any injection attempts were blocked (security signal requiring user awareness)

This keeps the alignment score visible and prevents silent drift.

---

## 4. Once Weekly

Run these on the first heartbeat of each week (use `weeklyGatewayVerify` timestamp to gate):

### 4.1 Gateway Security Verification

- [ ] Gateway is bound to loopback only (`127.0.0.1`, not `0.0.0.0`)
- [ ] Gateway auth is enabled and token is non-empty
- [ ] TLS is enforced for all non-local connections
- [ ] Audit log is non-empty and has entries from the past 7 days
- [ ] Risk score thresholds have not been changed from approved baseline

If any check fails, alert the user immediately regardless of time of day.

### 4.2 Skill Inventory Review

- List all currently enabled skills.
- Flag any skills that were added since the last weekly review.
- For new skills, re-run the provenance checklist from AGENTS.md Section 2.2.
- Report the inventory to the user in a brief weekly digest.

### 4.3 Sub-Agent Activity Summary

- Summarize sub-agent spawns from the past 7 days: count, task types, failure rate.
- Flag any sub-agent that failed more than once on the same task type (pattern indicator).

---

## 5. Heartbeat Failure Handling

If the heartbeat itself fails mid-run:

1. Log how far it got to heartbeat-state.json.
2. Send a direct message to the user: "Heartbeat failed at `<checkpoint>`. Partial results logged. Manual review recommended."
3. Do not retry automatically until the next scheduled cycle.
4. On the next run, re-run all checks that did not complete, regardless of their schedule tier.

---

## 6. Notification Standards for Heartbeats

All heartbeat notifications follow the standard priority queue from TOOLS.md:

| Finding | Priority |
|---|---|
| Gateway security misconfiguration | Critical — immediate |
| Secret or credential found in logs | Critical — immediate |
| Persistent failure (3+ recurrences) | High — hourly batch |
| New cron failure | High — hourly batch |
| Memory index below 80% | Medium — 3-hour batch |
| Repo size warning | Medium — 3-hour batch |
| Memory synthesis opportunity | Low — daily digest |
| Love Equation drift indicator | Medium — 3-hour batch |

---

## 7. Why This File Exists

Misconfigured heartbeats can quietly burn through API budgets — but heartbeats with no health checks are worse. They run silently while the system accumulates failures, credential leaks, and alignment drift that nobody sees.

HEARTBEAT.md operationalizes AI SAFE²'s **Engage & Monitor** pillar into a concrete, scheduled protocol. The difference between monitoring and forensics is whether you find the problem before or after it causes harm. Heartbeats done correctly are the mechanism that turns "we noticed eventually" into "we caught it the next cycle."

---

*Part of the AI SAFE² OpenClaw Core File Standard.*  
*AI SAFE² = Sanitize & Isolate · Audit & Inventory · Fail-Safe & Recovery · **Engage & Monitor** · Evolve & Educate*
