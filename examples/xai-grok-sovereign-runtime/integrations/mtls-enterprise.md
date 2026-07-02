# mTLS + ZDR Enterprise Guide
## xAI/Grok Sovereign Runtime — Enterprise Configuration
**AI SAFE2 v3.0 | Cyber Strategy Institute**

---

## Architecture: Defense-in-Depth for Enterprise xAI Deployments

```
Developer Workstation / CI Runner
        │
        ▼
┌─────────────────────────────────┐
│    AI SAFE2 Sovereign Runtime   │  ← GK-SKILL, GK-HOOK, GK-PERM,
│    sovereign_xai_grok.py        │    GK-SAND, GK-MULTI, GK-HEAD
└──────────────┬──────────────────┘
               │ Pre-validated request
               ▼
┌─────────────────────────────────┐
│    mTLS Mutual Auth Layer       │  ← Client cert + server cert verification
│    /etc/grok/certs/             │    Certificate pinning for x.ai endpoints
└──────────────┬──────────────────┘
               │ Encrypted + authenticated
               ▼
┌─────────────────────────────────┐
│    xAI API (ZDR Endpoint)       │  ← Zero Data Retention: no prompt storage
│    api.x.ai + mTLS enabled      │    at inference layer
└─────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│    AI SAFE2 Audit Chain         │  ← Local SHA-256 JSONL complements ZDR:
│    reports/nexus-audit.jsonl    │    ZDR removes from xAI, SAFE2 retains
└─────────────────────────────────┘   locally for compliance evidence
```

**ZDR + AI SAFE2 are complementary, not redundant.**
ZDR ensures no prompts persist at xAI's inference layer.
The AI SAFE2 audit chain provides the local evidence record that ZDR
removes from the xAI side. Satisfies CMMC 2.0 and FedRAMP audit requirements.

---

## mTLS Configuration

xAI supports mutual TLS for enterprise API access. Configure before production:

```python
import ssl
import httpx
from pathlib import Path

# Enterprise mTLS client
ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
ssl_context.load_verify_locations("/etc/grok/certs/xai-ca.crt")
ssl_context.load_cert_chain(
    certfile="/etc/grok/certs/client.crt",
    keyfile="/etc/grok/certs/client.key",
)
ssl_context.verify_mode = ssl.CERT_REQUIRED

client = httpx.Client(
    base_url="https://api.x.ai/v1",
    verify=ssl_context,
)

# Combine with AI SAFE2 sovereign runtime
from enforcement.sovereign_xai_grok import GrokSovereignRuntime

guard = GrokSovereignRuntime(required_sandbox_profile="strict")

def sovereign_xai_call(prompt: str) -> str:
    """AI SAFE2 + mTLS enforced call."""
    # P1.T1.2: Pre-call injection scan
    guard.scan_prompt(prompt)

    resp = client.post("/chat/completions", json={
        "model": "grok-4",
        "messages": [{"role": "user", "content": prompt}],
    })
    output = resp.json()["choices"][0]["message"]["content"]

    # P1.T1.4_ADV: Post-call secret leak scan
    guard.scan_response(output)

    return output
```

---

## Enterprise requirements.toml Template

Copy to `/etc/grok/requirements.toml` (root-owned, mode 600):

```toml
# /etc/grok/requirements.toml
# AI SAFE2 v3.0 Enterprise Baseline
# Root-owned. This file takes precedence over all user config.

[grok_com_config]
disable_api_key_auth = true
force_login_team_uuid = "YOUR-TEAM-UUID"

[ui]
disable_bypass_permissions_mode = true   # GK-PERM: prevents UI bypass

[sandbox]
profile = "workspace"                    # GK-SAND: minimum floor

[permission]
rules = [
  { action = "allow", tool = "read" },
  { action = "allow", tool = "bash", pattern = "git status" },
  { action = "allow", tool = "bash", pattern = "git log *" },
  { action = "allow", tool = "bash", pattern = "git diff *" },
  { action = "allow", tool = "bash", pattern = "npm test" },
  { action = "allow", tool = "bash", pattern = "python -m pytest *" },
  { action = "deny",  tool = "bash", pattern = "*" },      # deny all other bash
  { action = "deny",  tool = "web_fetch", pattern = "*" }, # network: explicit allows only
]

# GK-MULTI: Organization-wide multi-agent caps
[multi_agent]
max_agent_count = 4
require_approval_above = 2
```

---

## Certificate Rotation Procedure

xAI enterprise certificates should rotate on a 90-day cadence (P1.T2.9):

```bash
#!/bin/bash
# /etc/grok/scripts/rotate-certs.sh
# Run via cron: 0 0 1 */3 * /etc/grok/scripts/rotate-certs.sh

set -euo pipefail

CERT_DIR="/etc/grok/certs"
BACKUP_DIR="/etc/grok/certs/backup/$(date +%Y%m%d)"

mkdir -p "$BACKUP_DIR"
cp "$CERT_DIR/client.crt" "$BACKUP_DIR/"
cp "$CERT_DIR/client.key" "$BACKUP_DIR/"

# Generate new client certificate (adapt to your PKI)
openssl genrsa -out "$CERT_DIR/client.key.new" 4096
openssl req -new -key "$CERT_DIR/client.key.new" \
  -subj "/CN=grok-enterprise-client/O=YOUR-ORG" \
  -out "$CERT_DIR/client.csr"

# Submit CSR to your enterprise CA, then:
# mv "$CERT_DIR/client.crt.signed" "$CERT_DIR/client.crt"
# mv "$CERT_DIR/client.key.new" "$CERT_DIR/client.key"
# chmod 600 "$CERT_DIR/client.key"

echo "[AI SAFE2 P1.T2.9] Certificate rotation completed: $(date)" \
  >> /var/log/grok-ai-safe2.log
```

---

## NHI Registration (CP.4)

Register each xAI/Grok deployment as a Non-Human Identity in your IAM:

```yaml
# NHI registry entry (A2.4: Dynamic Agent State Inventory)
nhi_registry:
  - nhi_id: "nhi-xai-grok-prod-01"
    platform: "xAI Grok"
    act_tier: ACT-3
    hear_authority: "security@yourorg.com"   # CP.10: named HEAR
    tool_authorizations:
      - "read"
      - "bash(git *)"
      - "bash(npm test)"
    sandbox_profile: "workspace"
    max_agent_count: 4
    credential_source: "/etc/grok/certs/client.crt"
    rotation_cadence_days: 90
    created: "2026-06-19"
    owner_of_record: "platform-engineering-team"
    review_date: "2026-09-19"
```

---

## Compliance Evidence Matrix

| Control | Evidence Produced | File |
|---|---|---|
| CP.10 HEAR | Named authority in requirements.toml | /etc/grok/requirements.toml |
| CP.9 ARG | max_agent_count enforced | policy.yaml + audit chain |
| A2.5 Trace | SHA-256 JSONL per session | reports/nexus-audit.jsonl |
| P1.T2.9 Creds | Certificate rotation log | /var/log/grok-ai-safe2.log |
| P1.T1.2 IPI | Violation entries in JSONL | reports/ |
| F3.2 Governor | Turn ceiling in audit chain | reports/ |
| M4.4 Escalation | Real-time stderr + SIEM | Forward reports/ to SIEM |
