# AI SAFE² Gateway — Hermes Sovereign Runtime
### LLM Enforcement Proxy · P1 + P2 + P3 + P4

---

## What This Does

Every request from Hermes to any LLM provider passes through this proxy first.
The gateway enforces AI SAFE² v3.0 controls at the semantic layer — the only layer
where prompt injection, credential exfiltration, and oversized context attacks can be caught.

```
Hermes Agent → AI SAFE² Gateway (you are here) → Upstream LLM (Anthropic/OpenAI/etc.)
```

**Without the gateway:** Hermes sends requests directly to the LLM. Credentials in context,
injection patterns in retrieved content, and oversized requests all reach the model unfiltered.

**With the gateway:** Every request is filtered, risk-scored, and logged before touching the LLM.

---

## Controls Enforced

| Control | What It Blocks | AI SAFE² Ref |
|---|---|---|
| PII filter | SSNs, credit card numbers before LLM context | P1.S-C02 |
| Secrets filter | API keys, private keys, AWS credentials | P1.S-C02 |
| Injection filter | "Ignore instructions", identity replacement patterns | P1.S-C05 |
| Request size limit | Context window flooding attacks | P1.S-C02 |
| Tool allowlist | Unauthorized tool invocations | P3.F-C05 |
| Kill switch check | Halts all requests when activated | P3.F-C05 |
| Immutable audit log | Append-only HMAC-chained audit trail | P2.A-C05 |
| Taint tracking | Tags external-surface content before LLM injection | P1.S-C05 |

---

## Quick Start

```bash
# Install dependencies
pip install flask requests pyyaml --break-system-packages

# Set required environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export AUDIT_CHAIN_KEY="$(openssl rand -hex 32)"

# Configure Hermes to route through gateway
export ANTHROPIC_BASE_URL="http://127.0.0.1:8000/v1"

# Start gateway
python3 gateway.py
```

### Verify it's working

```bash
# Health check
curl http://127.0.0.1:8000/hsr/health

# Test PII filter
curl -X POST http://127.0.0.1:8000/hsr/scan \
  -H "Content-Type: application/json" \
  -d '{"text": "My SSN is 123-45-6789"}'
# Expected: {"findings": [{"type": "pii", ...}], "clean": false}

# Test secrets filter
curl -X POST http://127.0.0.1:8000/hsr/scan \
  -H "Content-Type: application/json" \
  -d '{"text": "sk-ant-api03-AAABBBCCC..."}'
# Expected: {"findings": [{"type": "secret", ...}], "clean": false}

# View recent audit events
curl http://127.0.0.1:8000/hsr/audit/tail?n=10 | python3 -m json.tool
```

---

## Provider Configuration

Edit `config.yaml` to switch providers:

```yaml
provider:
  active: "anthropic"  # or: openai | openrouter | gemini | ollama | nim
```

Set the corresponding API key in environment:

```bash
# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# OpenRouter (200+ models)
export OPENROUTER_API_KEY="sk-or-..."

# Ollama (local, no key needed)
# provider.active: ollama in config.yaml
```

---

## Management API

| Endpoint | Method | Description |
|---|---|---|
| `/hsr/health` | GET | Gateway status, config, uptime |
| `/hsr/audit/tail?n=N` | GET | Last N audit events |
| `/hsr/scan` | POST | Test content against filters |
| `/hsr/kill` | POST | Activate kill switch |
| `/hsr/revive` | POST | Deactivate kill switch |

---

## Kill Switch

```bash
# Via management API
curl -X POST http://127.0.0.1:8000/hsr/kill \
  -H "Content-Type: application/json" \
  -d '{"reason": "Suspected injection attack in session XYZ"}'

# Via script (also pauses Docker container)
bash ../scripts/kill-switch.sh "Suspected injection attack"

# Revive
bash ../scripts/kill-switch.sh --revive
```

---

## Audit Log Format

Every proxied request generates an append-only audit entry:

```json
{
  "event": "request_proxied",
  "request_id": "hsr-1748200000001",
  "timestamp": "2026-05-25T14:00:00.000Z",
  "model": "claude-sonnet-4-20250514",
  "provider": "anthropic",
  "status_code": 200,
  "duration_ms": 847,
  "findings_count": 0,
  "path": "/v1/messages",
  "prev_hash": "abc123...",
  "hash": "def456..."
}
```

Each entry includes `prev_hash` and `hash` for HMAC chain integrity verification.
Tampering with any entry breaks the chain.

---

## Files

| File | Purpose |
|---|---|
| `gateway.py` | Main Flask proxy application |
| `provider_adapters.py` | Multi-provider request/response translation |
| `scanner.py` | Skill/memory/dependency anomaly scanner |
| `config.yaml` | Gateway configuration |

---

*AI SAFE² Gateway · Hermes Sovereign Runtime · Cyber Strategy Institute*
