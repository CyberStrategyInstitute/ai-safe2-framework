# AI SAFE2 v3.0 MCP Server
## Setup, Deployment, and Client Configuration

The AI SAFE2 MCP server exposes 7 tools, 2 MCP resources, and 2 MCP prompts
backed by the complete 161-control AI SAFE2 v3.0 taxonomy. It connects Claude Code,
Codex, and any MCP-compatible client to live control lookup, risk scoring, compliance
mapping, and governance resources.

**Two transports — both secure:**
- `stdio`: local use, inherently secure (OS process pipe), no auth required
- `streamable-http` over HTTPS: remote access via Caddy TLS termination, bearer token auth

---

## Tiered Access

Tokens are issued at **cyberstrategyinstitute.com/ai-safe2/** — the server only validates.

| Feature | Free Tier | Pro Tier (Toolkit) |
|---------|-----------|-------------------|
| Token | Email registration | Toolkit purchase ($97) |
| Control lookup | 30 controls per query | 500 controls per query |
| Compliance mapping | 5 frameworks | All 32 frameworks |
| Risk scoring | CVSS + Pillar (no AAF) | Full AAF formula |
| Code review | No | Yes |
| Agent classification | ACT-1/ACT-2 only | Full ACT-1 through ACT-4 |
| Policy templates | 3 resources | All resources |
| Rate limit | 30 req/hour | 1000 req/hour |
| Local stdio | Yes (always Pro access) | Yes |

---

## Option 1: Local stdio Setup (5 minutes, no token)

Stdio is a local OS process pipe — no network port, no auth needed, inherently
scoped to your machine. Full Pro access locally.

### Prerequisites
- Python 3.11+
- The ai-safe2-framework repo cloned locally

### Install and run

```bash
# From the repo root
cd skills/mcp

# Install dependencies
pip install -e .

# Run the server (stdio transport)
MCP_TRANSPORT=stdio python -m mcp_server.app
```

### Connect Claude Code

Add to Claude Code settings (`~/.cursor/settings.json` or equivalent):
```json
{
  "mcpServers": {
    "ai-safe2": {
      "command": "python",
      "args": ["-m", "mcp_server.app"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "PYTHONPATH": "/your/path/to/ai-safe2-framework/skills/mcp/src"
      }
    }
  }
}
```

### Connect via Docker (stdio)

```bash
# Build the image
docker build -t ai-safe2-mcp .

# Run stdio (works as a subprocess for any MCP client)
docker run --rm -i -e MCP_TRANSPORT=stdio ai-safe2-mcp
```

Docker config for Claude Code:
```json
{
  "mcpServers": {
    "ai-safe2": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "-e", "MCP_TRANSPORT=stdio", "ai-safe2-mcp"]
    }
  }
}
```

---

## Option 2: Railway Deployment (15 minutes, HTTPS automatic)

Railway provides Docker-native deployment with automatic HTTPS and a public URL.

### Deploy steps

1. **Fork or push this repo to GitHub**

2. **Create a new Railway project**
   - Go to railway.app, create project, select "Deploy from GitHub repo"
   - Point to your fork of ai-safe2-framework

3. **Set the root directory** to `skills/mcp` in Railway settings

4. **Set environment variables in Railway dashboard:**
   ```
   MCP_TRANSPORT=streamable-http
   MCP_HOST=0.0.0.0
   MCP_PORT=8000
   LOG_LEVEL=INFO
   LOG_FORMAT=json
   TOKENS=free_yourtoken123:free,pro_yourtoken456:pro
   ```

5. **Railway provides automatic HTTPS** — your endpoint will be:
   `https://your-app.up.railway.app/mcp`

6. **Test the health endpoint:**
   ```bash
   curl https://your-app.up.railway.app/health
   ```
   Expected: `{"status": "healthy", "controls_loaded": 161, ...}`

### Note on Caddy with Railway
Railway handles TLS automatically — you do not need the Caddy sidecar.
The `docker-compose.yml` with Caddy is for self-hosted VPS deployments.
On Railway, set `MCP_HOST=0.0.0.0` so Railway can forward traffic to the container.

---

## Option 3: Self-Hosted VPS with Caddy (HTTPS, full control)

For production self-hosting with your own domain.

### Prerequisites
- VPS with Docker and Docker Compose installed
- Domain DNS A record pointing to your VPS IP

### Setup

```bash
# Clone the repo
git clone https://github.com/CyberStrategyInstitute/ai-safe2-framework.git
cd ai-safe2-framework/skills/mcp

# Configure environment
cp .env.example .env
# Edit .env:
#   DOMAIN=mcp.yourdomain.com
#   TOKENS=free_abc:free,pro_xyz:pro

# Build and start (Caddy handles HTTPS automatically)
docker compose up -d

# Verify health
curl https://mcp.yourdomain.com/health
```

Caddy automatically obtains a Let's Encrypt certificate for your domain.
First startup takes ~30 seconds for certificate provisioning.

---

## Token Management

Tokens follow the format: `{tier_prefix}_{random_string}`
- Free prefix: `free_`
- Pro prefix: `pro_`

Set in the server via the `TOKENS` environment variable:
```
TOKENS=free_abc123def:free,pro_xyz789uvw:pro,pro_another:pro
```

For production with many users, replace the `TOKEN_MAP` in `config.py` with
a database lookup or external token service. The auth middleware in `auth.py`
calls `TOKEN_MAP.get(token)` — swap this for any validation backend.

**The server never issues tokens.** All token issuance happens at
cyberstrategyinstitute.com/ai-safe2/ — this keeps the MCP server stateless
and simple.

---

## Connect Codex

```toml
# ~/.codex/config.toml
experimental_use_rmcp_client = true

[mcp_servers.ai-safe2]
url = "https://your-domain.example/mcp"
bearer_token = "YOUR_TOKEN_HERE"
startup_timeout_sec = 20
tool_timeout_sec = 60
```

For local stdio with Codex:
```toml
[mcp_servers.ai-safe2-local]
command = "python"
args = ["-m", "mcp_server.app"]
env = { MCP_TRANSPORT = "stdio", PYTHONPATH = "/path/to/skills/mcp/src" }
```

---

## Available Tools (Quick Reference)

### `lookup_control`
```
query: str          — keyword search across name, description, tags, builder_problem
control_id: str     — exact ID lookup (e.g., "CP.10", "S1.5", "F3.2")
pillar: str         — "P1" through "P5" or "CP"
priority: str       — "CRITICAL", "HIGH", "MEDIUM", "LOW"
framework: str      — e.g., "EU_AI_Act", "SOC2_Type2", "OWASP_Agentic_Top10"
version_added: str  — "v2.0", "v2.1", "v3.0"
act_tier: str       — "ACT-1", "ACT-2", "ACT-3", "ACT-4"
```

### `risk_score`
```
cvss_base: float       — CVSS base score (0-10)
pillar_score: float    — AI SAFE2 compliance score (0-100)
aaf_factors: dict      — OWASP AIVSS v0.8 factors (Pro only)
```

### `compliance_map`
```
requirement: str       — e.g., "EU AI Act Article 14", "GDPR Article 22", "SOC 2 CC.7.4"
framework_ids: list    — filter to specific frameworks (optional)
```

### `code_review` (Pro)
```
code: str              — code to review
language: str          — "python", "javascript", "typescript", etc.
context: str           — what this code does (optional)
focus_pillar: str      — "P1" through "P5" (optional, reviews all if omitted)
```

### `agent_classify`
```
description: str                — what the agent does
human_review_required: bool     — must human review all outputs?
spawns_sub_agents: bool         — can this agent spawn other agents?
has_persistent_memory: bool     — cross-session state?
tool_access: list               — tools the agent can call
operates_unattended: bool       — runs without human presence?
deployment_environment: str     — "production", "enterprise", etc.
```

### `get_governance_resource`
```
resource_name: str    — resource ID, or empty string to list available resources
                        Free: quick_start_checklist, pillar_overview, act_tier_reference
                        Pro: governance_policy_template, audit_scorecard_schema,
                             hear_designation_template
```

### `get_workflow_prompt`
```
prompt_name: str      — or empty to list all prompts
arguments: dict       — template variables (see prompt definitions)
Available: security_architecture_review, compliance_gap_analysis,
           incident_response_runbook, agent_deployment_checklist
```

---

## Running Tests

```bash
cd skills/mcp

# Unit tests (no server needed)
pytest tests/test_tools.py -v

# HTTPS smoke tests (requires deployed instance)
MCP_SERVER_URL=https://your-domain.example \
MCP_PRO_TOKEN=pro_your_token \
MCP_FREE_TOKEN=free_your_token \
pytest tests/test_smoke_https.py -v
```

Expected unit test result: all tests pass, including:
- `test_loads_161_controls` — confirms JSON integrity
- `test_loads_32_frameworks` — confirms framework count
- `test_pro_gate_on_aaf` — confirms tier enforcement

---

## Security Architecture

```
Internet
    │ HTTPS (443)
    ▼
Caddy (TLS termination, HSTS, security headers, rate limiting)
    │ HTTP (127.0.0.1:8000, internal only)
    ▼
MCP Server (BearerAuthMiddleware → FastMCP tools)
    │
    ├── stdio transport: local process pipe, no network, no auth
    └── HTTP transport: binds to 127.0.0.1 only, Caddy is the only caller
```

**Key security properties:**
- MCP server never exposed on a public port — Caddy is the only gateway
- Bearer tokens validated on every request — middleware, not optional
- stdio mode: no network, no credentials needed, scoped to local process
- Non-root Docker user (UID 1001)
- No code execution on server — code review is model-based only
- Tokens never stored in code — environment variables only

---

## Updating the Controls

To update the control taxonomy:

```bash
cd skills/mcp/data

# Edit generate_controls.py to add or modify controls
# Then regenerate:
python generate_controls.py

# Verify count
python -c "
import json
with open('ai-safe2-controls-v3.0.json') as f:
    d = json.load(f)
print('Total:', d['metadata']['total_controls'])
"

# Run tests
cd .. && pytest tests/test_tools.py -v
```

The `ControlsDB` class reloads on startup — no code changes needed when
the JSON is updated, just restart the server.

---

*AI SAFE2 v3.0 | Cyber Strategy Institute | cyberstrategyinstitute.com/ai-safe2/*
*github.com/CyberStrategyInstitute/ai-safe2-framework*
