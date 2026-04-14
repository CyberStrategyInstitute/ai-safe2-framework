# AI SAFE² Core Gateway — v3.0

**FastAPI async gateway implementing the full AI SAFE² v3.0 enforcement stack.**  
Drop this in front of any Anthropic API consumer. Every request is risk-scored, HITL-gated, and immutably logged before it ever reaches the upstream.

---

## Architecture

```
Client → [HeartbeatMonitor] → [RateLimiter] → [RiskScorer] → [HITL Gate] → Upstream API
                                                                      ↓
                                                          [ImmutableAuditLog]
                                                                      ↓
                                                          [ResponseScanner] → Client
```

### Enforcement components

| Component | Function |
|-----------|----------|
| `HeartbeatMonitor` | Validates `HEARTBEAT.md` freshness before every request. Missing, empty, or stale → safe mode. Never auto-creates. |
| `ImmutableAuditLog` | HMAC-SHA256 chained JSONL. Each entry links to the previous hash. Startup chain verification. Break → safe mode. |
| `RiskScorer` | 3-vector composite: action\_type (0.40) × target\_sensitivity (0.35) × historical\_context (0.25). +5 injection, +3 A2A. Capped 10.0. |
| `HITLCircuitBreaker` | 4-tier: AUTO (0–3) / MEDIUM (4–6, token) / HIGH (7–8, token + reason ≥20 chars) / CRITICAL (>8, HMAC 2FA challenge). |
| `ResponseScanner` | Inspects every upstream response for exfil patterns and tool\_use injection payloads before returning to client. |
| `SafeMode` | Event-based hard stop. Activated by heartbeat failure or chain break. Deactivated only by operator key — never by agent. |

---

## Quick start

### 1. Prerequisites

```bash
python3 -m pip install fastapi uvicorn httpx pyyaml
```

### 2. Environment variables

```bash
export ANTHROPIC_API_KEY="sk-ant-api..."                  # upstream key
export AUDIT_CHAIN_KEY="$(openssl rand -hex 32)"          # HMAC signing key — store securely
export OPERATOR_DEACTIVATION_KEY="$(openssl rand -hex 16)" # safe mode recovery
export ALERT_WEBHOOK_URL="https://hooks.slack.com/..."    # optional
```

### 3. Initialize heartbeat (first run only)

```bash
python3 -c "
from gateway.main import HeartbeatMonitor
m = HeartbeatMonitor('HEARTBEAT.md')
m.initialize_once()
print('Heartbeat initialized.')
"
```

### 4. Run

```bash
uvicorn gateway.main:app --host 127.0.0.1 --port 8080
```

Point your Anthropic SDK at `http://localhost:8080` and set `base_url` accordingly.

---

## HITL tier reference

| Tier | Score | Client requirement |
|------|-------|--------------------|
| AUTO | 0–3 | None |
| MEDIUM | 4–6 | `X-HITL-Token: <token>` (token returned on first 403) |
| HIGH | 7–8 | `X-HITL-Token` + `X-HITL-Reason` (≥ 20 characters) |
| CRITICAL | > 8 | Out-of-band 2FA: `HMAC-SHA256(AUDIT_CHAIN_KEY, challenge_token)[:16]` |

---

## Risk vector scoring

**Action type** (tool names / message keywords):

| Score | Tier | Examples |
|-------|------|---------|
| 0 | Read | `read`, `search`, `get`, `list` |
| 5 | Write | `write`, `create`, `update`, `send` |
| 10 | Exec/Delete | `execute`, `delete`, `run`, `deploy`, `kill` |

**Target sensitivity** (content patterns):

| Score | Classification |
|-------|---------------|
| 0 | Public / generic |
| 5 | Personal data (`/home/`, `Documents/`, `private`) |
| 10 | System / credentials (`/etc/`, `.ssh/`, `SECRET`, `TOKEN`) |

**Historical context** (per user+fingerprint frequency):

| Score | Frequency |
|-------|-----------|
| 0 | Frequent (≥ 5 seen) |
| 5 | Rare (< 5 seen) |
| 10 | Never seen |

---

## Audit log

Entries are written to `logs/audit.jsonl` as HMAC-SHA256 chained JSONL:

```json
{
  "seq": 1,
  "timestamp": "2025-01-01T00:00:00.000000+00:00",
  "gateway_version": "3.0.0",
  "framework": "AI SAFE² v3.0",
  "user_id": "user@example.com",
  "request_hash": "sha256:...",
  "risk_score": 4.25,
  "risk_vectors": {"action_type": 5.0, "target_sensitivity": 5.0, "historical_context": 5.0},
  "hitl_tier": "MEDIUM",
  "blocked": false,
  "reason": null,
  "entry_hash": "sha256:..."
}
```

Verify chain integrity at any time:

```bash
python3 -c "
from gateway.main import ImmutableAuditLog
import os
log = ImmutableAuditLog('logs/audit.jsonl', os.environ['AUDIT_CHAIN_KEY'])
ok, count, msg = log.verify_chain()
print(f'Chain: {\"OK\" if ok else \"BROKEN\"} — {count} entries — {msg}')
"
```

---

## Safe mode

Safe mode blocks **all** traffic until an operator explicitly deactivates it.

```bash
# Deactivate via API (requires OPERATOR_DEACTIVATION_KEY)
curl -X POST http://localhost:8080/emergency/deactivate-safe-mode \
  -H "X-Operator-Key: $OPERATOR_DEACTIVATION_KEY"
```

Triggers: missing/empty/stale `HEARTBEAT.md`, audit chain break, operator invocation.

---

## Health endpoint

```bash
curl http://localhost:8080/health
```

```json
{
  "status": "healthy",
  "safe_mode": false,
  "heartbeat_valid": true,
  "framework": "AI SAFE² v3.0"
}
```

---

## Framework reference

AI SAFE² v3.0 · Cyber Strategy Institute · [github.com/CyberStrategyInstitute/ai-safe2-framework](https://github.com/CyberStrategyInstitute/ai-safe2-framework)
