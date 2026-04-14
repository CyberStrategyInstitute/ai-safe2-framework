# AI SAFE² Core Gateway — v3.0

**AI enforcement proxy implementing the full AI SAFE² v3.0 governance stack.**
Supports multiple LLM providers. Every request is risk-scored, HITL-gated, and immutably logged before it reaches the upstream — regardless of which provider is active.

---

## Architecture

```
Client Request
      │
      ▼
[HeartbeatMonitor]      ← hard stop if HEARTBEAT.md missing / stale / tampered
      │
[RateLimiter]           ← per-identity sliding window (rpm + rph)
      │
[ProviderAdapter]       ← normalize request; extract NEXUS-A2A fields if present
      │
[RiskScorer]            ← 3-vector composite: action × sensitivity × history
      │
[HITLCircuitBreaker]    ← AUTO / MEDIUM / HIGH / CRITICAL tier enforcement
      │
[ImmutableAuditLog]     ← HMAC-SHA256 chained JSONL — every decision recorded
      │
[Provider Dispatch]     ← forward to active provider
      │
[ResponseScanner]       ← exfil + tool_use injection check on upstream response
      │
      ▼
Client Response
```

### Enforcement components

| Component | Function |
|-----------|----------|
| `HeartbeatMonitor` | Validates `HEARTBEAT.md` freshness before every request. Missing, empty, or stale → safe mode. Never auto-creates. |
| `ImmutableAuditLog` | HMAC-SHA256 chained JSONL. Tamper detection on startup. Chain break → safe mode. |
| `RiskScorer` | 3-vector composite: action\_type (0.40) × target\_sensitivity (0.35) × historical\_context (0.25). +5 injection, +3 A2A. Capped 10.0. |
| `HITLCircuitBreaker` | 4-tier: AUTO (0–3) / MEDIUM (4–6, token) / HIGH (7–8, token + reason ≥20 chars) / CRITICAL (>8, HMAC 2FA challenge). |
| `ProviderAdapter` | Normalizes requests across providers for enforcement. Forwards original payload untouched. |
| `ResponseScanner` | Inspects every upstream response for exfil patterns and tool\_use injection payloads before returning to client. |
| `SafeMode` | Event-based hard stop. Activated by heartbeat failure or chain break. Operator-key deactivation only. |

---

## Files

```
gateway/
├── main.py                 # FastAPI async enforcement proxy
├── provider_adapters.py    # Multi-provider adapter layer (Anthropic, OpenAI, Gemini, Ollama, OpenRouter)
├── README.md               # This file
└── HEARTBEAT.md            # Created on first run via --init-heartbeat (never auto-created)
```

`provider_adapters.py` must be in the same directory as `main.py`. If absent, the gateway falls back to Anthropic-only mode with a warning at startup.

---

## Quick start

### 1. Prerequisites

```bash
python3 -m pip install fastapi uvicorn httpx pyyaml requests
```

### 2. Environment variables

`AUDIT_CHAIN_KEY` and `OPERATOR_DEACTIVATION_KEY` are always required. Set the API key for your active provider.

```bash
export AUDIT_CHAIN_KEY="$(openssl rand -hex 32)"
export OPERATOR_DEACTIVATION_KEY="$(openssl rand -hex 16)"
export ALERT_WEBHOOK_URL="https://hooks.slack.com/..."     # optional

# Anthropic (default)
export ANTHROPIC_API_KEY="sk-ant-api..."

# OpenAI
# export OPENAI_API_KEY="sk-..."

# Gemini
# export GEMINI_API_KEY="AIza..."

# OpenRouter
# export OPENROUTER_API_KEY="sk-or-..."

# Ollama (local) — no API key required
```

### 3. Set active provider

Edit the default config in `main.py` or pass via environment:

```python
"provider": {"active": "anthropic"}   # anthropic | openai | gemini | ollama | openrouter
```

### 4. Initialize heartbeat (first run only)

```bash
python3 -c "
from gateway.main import HeartbeatMonitor
m = HeartbeatMonitor('HEARTBEAT.md')
m.initialize_once()
print('Heartbeat initialized.')
"
```

### 5. Run

```bash
uvicorn gateway.main:app --host 127.0.0.1 --port 8080
```

Point your SDK's `base_url` at `http://localhost:8080/v1/messages`.

---

## Multi-provider support

All enforcement controls operate identically regardless of provider. The adapter handles auth headers and response format normalization transparently — the original request payload is always forwarded untouched.

| Provider | Client format | API key env var |
|----------|--------------|-----------------|
| `anthropic` | Anthropic Messages API | `ANTHROPIC_API_KEY` |
| `openai` | OpenAI Chat Completions | `OPENAI_API_KEY` |
| `gemini` | Gemini generateContent | `GEMINI_API_KEY` |
| `ollama` | OpenAI-compatible (local) | none by default |
| `openrouter` | OpenAI-compatible | `OPENROUTER_API_KEY` |

**Ollama:** pull a model first with `ollama pull llama3`, then set `providers.ollama.model` in config.

**OpenRouter:** supports 100+ models via a single endpoint and billing account. Set `model` to any [OpenRouter model ID](https://openrouter.ai/models), e.g. `"anthropic/claude-sonnet-4-20250514"`, `"openai/gpt-4o"`, `"meta-llama/llama-3.1-70b"`.

---

## NEXUS-A2A compatibility

The gateway includes NEXUS-A2A v0.2 compatibility hooks. No NEXUS runtime required.

**Active now:**
- NEXUS header detection and logging (`x-nexus-agent-id`, `x-nexus-session-id`, `x-nexus-delegation-chain`, etc.)
- A2A detection upgraded to NEXUS-aware indicator set (includes NEXUS v0.2 canonical message types)
- NEXUS identity fields written to every audit log entry when present

**When NEXUS ships:** flip one config value — no code changes required.

```python
"nexus": {"enabled": True, "enforcement": "passthrough"}
# → "enforcement": "verify"  or  "enforcement": "enforce"
```

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

Entries written to `logs/audit.jsonl` as HMAC-SHA256 chained JSONL. NEXUS identity fields appended when present.

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
  "provider": "openai",
  "nexus_agent_id": "did:nexus:abc123",
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
  "active_provider": "anthropic",
  "framework": "AI SAFE² v3.0"
}
```

---

## Framework reference

AI SAFE² v3.0 · Cyber Strategy Institute · [github.com/CyberStrategyInstitute/ai-safe2-framework](https://github.com/CyberStrategyInstitute/ai-safe2-framework)
