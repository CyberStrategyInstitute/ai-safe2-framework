# Incident Response Runbooks
### Hermes Sovereign Runtime · AI SAFE² v3.0

**Keep this file accessible offline.** When an incident is active, you may not
want to rely on Hermes to read it to you.

---

## Runbook Index

1. [Credential Exfiltration Suspected](#1-credential-exfiltration)
2. [Memory Injection Detected](#2-memory-injection)
3. [Kill Switch Activation](#3-kill-switch)
4. [Skill Injection Detected](#4-skill-injection)
5. [Subagent Scope Breach](#5-subagent-scope-breach)
6. [Gateway Unavailable](#6-gateway-unavailable)
7. [Anomalous Tool Call Volume](#7-anomalous-tool-calls)

---

## 1. Credential Exfiltration

**Triggers:** Memory auditor finds credential pattern in memory store. Scanner finds credential
path access in skill. Audit log shows read_file call against `~/.ssh/`, `~/.aws/`, or `.env`.

**Immediate Response (first 5 minutes):**

```bash
# Step 1: Kill switch
bash scripts/kill-switch.sh "Credential exfiltration suspected"

# Step 2: Rotate ALL credentials that Hermes had access to
bash scripts/rotate-credentials.sh

# Step 3: Preserve evidence
cp ~/.hermes/memories/*.md /tmp/incident-$(date +%s)/
docker exec hsr-hermes cp -r /home/hermes/.hermes /tmp/incident-$(date +%s)/ 2>/dev/null || true
```

**Investigation:**

```bash
# Find the session that accessed the credential
grep "read_file\|file_read" /var/log/hsr/audit.jsonl | python3 -m json.tool | grep -A5 "ssh\|aws\|env\|credential"

# Find when the memory was written
grep "memory_write\|EXTERNAL-SOURCE" /var/log/hsr/audit.jsonl | tail -50

# Check which adapter session delivered the content
grep "telegram\|discord\|slack\|email\|web" /var/log/hsr/audit.jsonl | tail -100
```

**Recovery:**
1. Rotate all affected credentials (see rotate-credentials.sh)
2. Purge affected memory entries
3. Verify vaccine file is loaded correctly
4. Run Pass 3 adversarial tests before reactivating
5. Document timeline for compliance report

---

## 2. Memory Injection Detected

**Triggers:** Memory auditor reports injection pattern in SQLite or memory file.
Hermes behaves unexpectedly after a web retrieval or email processing session.

**Immediate Response:**

```bash
# Run targeted memory scan
python3 monitoring/memory_auditor.py --quarantine

# Check what the auditor found
cat /tmp/hsr_memory_audit.jsonl | python3 -m json.tool | tail -50

# Manual inspection of suspicious memory file
cat ~/.hermes/memories/[suspicious_file].md
```

**Quarantine:**

```bash
# Move suspicious files
mkdir -p /tmp/hsr-quarantine/$(date +%Y%m%d)
mv ~/.hermes/memories/[suspicious_file].md /tmp/hsr-quarantine/$(date +%Y%m%d)/

# For SQLite: find and delete affected rows
sqlite3 ~/.hermes/memories/hermes.db "DELETE FROM memories WHERE rowid=[row_id];"
```

**Root Cause:**
- Which external session wrote the injection? Check session timestamps vs. memory write times.
- What content source (web page, email, document) carried the injection payload?
- Was it retrieved via the gateway (taint-tagged) or via a direct tool call?

**Prevention:**
- Verify taint-tracking is enabled in `gateway/config.yaml`
- Verify vaccine is loading at highest priority (filename: `000_VACCINE_sovereign.md`)
- Enable `--quarantine` flag in memory auditor watch mode

---

## 3. Kill Switch Activation

**When to use:**
- Suspected active attack in progress
- Anomalous tool call patterns observed
- Credential exfiltration attempt detected
- Injection confirmed in memory store

**Activate:**

```bash
bash scripts/kill-switch.sh "Reason for activation"
```

**What happens:**
- Kill file written to `/tmp/hsr_kill_switch`
- Gateway returns 503 to all Hermes LLM requests
- `hsr-hermes` Docker container paused
- Alert webhook fired (if configured)
- Event logged to audit trail

**While kill switch is active:**
- Investigate the incident using audit logs
- Rotate credentials if suspected compromised
- Clean affected memory stores
- Run Pass 3 adversarial tests

**Reactivate only after:**

```bash
# Confirm all checks pass
bash validation/pass1_static.sh
python3 validation/pass3_adversarial.py

# Then revive
bash scripts/kill-switch.sh --revive
```

---

## 4. Skill Injection Detected

**Triggers:** Scanner finds malicious pattern in skill file. Hermes installs an unsigned skill.
Skill attempts credential access or spawns unexpected subprocesses.

**Immediate:**

```bash
# Quarantine the skill
mkdir -p /tmp/hsr-quarantine/skills
mv ~/.hermes/skills/[suspicious_skill].py /tmp/hsr-quarantine/skills/

# Run full skill scan
python3 gateway/scanner.py --skills --strict

# Check if skill has already executed
grep "[skill_name]" /var/log/hsr/audit.jsonl | python3 -m json.tool
```

**Identify origin:**
- Was the skill installed from agentskills.io (community hub) without review?
- Was installation suggested by web content, email, or gateway message?
- Check skill install timestamp vs. recent session activity

**Prevention:**
- All new skills must go through `skills-registry/verify_skill.sh` before installation
- Skills from community hub are UNTRUSTED until manually reviewed
- See `skills-registry/README.md` for sovereign registry workflow

---

## 5. Subagent Scope Breach

**Triggers:** Subagent attempts to use tools outside its declared scope.
Subagent output contains instructions (not data). Subagent attempts memory access.

**Response:**

```bash
# Terminate the subagent immediately
hermes subagent kill [subagent_id]  # Hermes CLI command

# Log the incident
echo "{\"event\":\"subagent_scope_breach\",\"subagent_id\":\"[id]\",\"timestamp\":\"$(date -u +%FT%TZ)\"}" >> /var/log/hsr/audit.jsonl

# Review subagent spawn declaration vs. actual behavior
grep "subagent_spawn\|subagent_[id]" /var/log/hsr/audit.jsonl
```

**Review SUBAGENT-POLICY.md:** Verify spawn declarations include explicit tool subsets.
Subagents should never receive wildcard capability inheritance.

---

## 6. Gateway Unavailable

**Hermes will fail to make LLM calls when gateway is down.**
This is intentional — fail-closed is correct behavior.

**Restart:**

```bash
# Docker
docker compose restart safe2-gateway
docker compose logs -f safe2-gateway

# Direct
python3 gateway/gateway.py &
```

**While gateway is down:**
- Hermes cannot make LLM API calls (by design — ANTHROPIC_BASE_URL points to gateway)
- Do NOT temporarily set ANTHROPIC_BASE_URL to direct API endpoint
- Fix the gateway, not the routing

---

## 7. Anomalous Tool Call Volume

**Triggers:** Prometheus/Grafana alert fires on 3σ deviation from baseline tool call rate.
Ishi supervisor anomaly score exceeds threshold.

**Investigation:**

```bash
# View recent tool calls
curl http://127.0.0.1:8000/hsr/audit/tail?n=100 | \
  python3 -c "import json,sys; [print(json.dumps(e,indent=2)) for e in json.load(sys.stdin)['events'] if 'tool' in str(e)]"

# Check for rate anomalies
grep "request_proxied" /var/log/hsr/audit.jsonl | \
  python3 -c "
import json, sys, collections
from datetime import datetime
counts = collections.Counter()
for line in sys.stdin:
    try:
        e = json.loads(line)
        counts[e.get('timestamp','')[:16]] += 1
    except: pass
for k,v in sorted(counts.items())[-20:]: print(f'{k}: {v} requests')
"
```

**Typical causes:**
- Cron job running without Ishi approval
- Runaway subagent loop
- Injection causing repeated tool calls

---

*HSR Incident Response Runbooks · Cyber Strategy Institute · AI SAFE² v3.0*
*Last updated: May 2026*
