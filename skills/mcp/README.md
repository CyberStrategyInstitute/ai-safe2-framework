# AI SAFE2 v3.0 — MCP Server

> **161 controls. 32 compliance frameworks. Live governance at the agent boundary.**
> Connect any MCP-compatible AI client to the AI SAFE2 v3.0 control taxonomy in minutes.

[![Version](https://img.shields.io/badge/AI_SAFE2-v3.0.1-orange)](https://cyberstrategyinstitute.com/ai-safe2/)
[![Controls](https://img.shields.io/badge/Controls-161-blue)]()
[![Frameworks](https://img.shields.io/badge/Frameworks-32-blue)]()
[![Tests](https://img.shields.io/badge/Tests-137_passing-brightgreen)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey)]()

---

## What This Is

The AI SAFE2 MCP server puts the full v3.0 control taxonomy inside Claude Code, Codex, Cursor, or any MCP-compatible agent — live, queryable, and enforcement-aware. Not documentation. Not a checklist. A governance runtime that answers the questions that matter at build time:

- *Can this agent ship?* — `agent_classify` returns ACT tier, mandatory controls, and kill conditions
- *What is the risk score?* — `risk_score` computes CVSS + Pillar + OWASP AIVSS AAF
- *Which controls apply?* — `lookup_control` queries 161 controls by keyword, pillar, framework, or ID
- *Does this map to my audit framework?* — `compliance_map` crosswalks to 32 frameworks instantly
- *Does this code meet the standard?* — `code_review` returns AI SAFE2-grounded findings

**7 tools. 2 transports. Free and Pro tiers. 5-minute local setup.**

---

## Quick-Start Guide

| Goal | Path | Time |
|------|------|------|
| Try it locally — Claude Code, no token needed | [Option 1 — Local stdio](#option-1--local-stdio-5-minutes) | 5 min |
| Connect Codex CLI locally | [Option 1b — Codex stdio](#connect-codex-cli-stdio) | 5 min |
| Deploy to the cloud for team access | [Option 2 — Railway](#option-2--railway-15-minutes) | 15 min |
| Self-hosted production with Caddy | [Option 3 — Caddy](#option-3--self-hosted-caddy-production) | 30 min |
| Get a Pro token | [cyberstrategyinstitute.com/ai-safe2](https://cyberstrategyinstitute.com/ai-safe2/) | — |
| Run all tests | [Testing](#running-tests) | 2 min |
| Security patch notes (v3.0.1) | [Security Architecture](#security-architecture) | — |

---

## Tier Comparison

Tokens are issued at **[cyberstrategyinstitute.com/ai-safe2/](https://cyberstrategyinstitute.com/ai-safe2/)** — the server only validates. It never issues tokens.

> **Local stdio always runs at Pro access. No token needed for local use.**

| Capability | Free | Pro |
|-----------|:----:|:---:|
| Token | Email registration | Toolkit ($97) |
| Control lookup | 30 per query | **500 per query** |
| Compliance frameworks | 5 | **All 32** |
| Risk scoring | CVSS + Pillar | **+ OWASP AIVSS AAF** |
| Code review | — | **Yes** |
| Agent classification | ACT-1 / ACT-2 | **ACT-1 through ACT-4** |
| Governance resources | 3 | **All** |
| Rate limit | 30 req/hour | **1,000 req/hour** |
| Sub-agent governance (CP.9) | — | **Yes** |
| HEAR Doctrine (CP.10) | — | **Yes** |
| Swarm defense mapping | — | **Yes** |
| Full AAF factor breakdown | — | **Yes** |

### Why Pro Matters at Scale

Free tier is a signal detector. Pro tier is an enforcement layer. The difference compounds with agent complexity.

| Deployment | Free | Pro |
|-----------|------|-----|
| **Single agent** — ACT-1/2, supervised | Initial control lookup | Full risk score + code review + all 32 frameworks |
| **Sub-agent chains** — ACT-3, automated | ACT tier blocked | CP.9 replication governance, HEAR Doctrine, kill-switch specs |
| **Small swarm** (up to 100 agents) | No swarm visibility | Swarm Defense Architecture across 8 defense domains |
| **Medium swarm** (101–500 agents) | Cannot map controls to execution boundaries | Full ACT-4 requirements, agent taxonomy, sovereignty scale |
| **Large swarm** (500+ agents) | No governance at scale | HEAR + CP.9 + CP.10 + lineage token propagation |

At ACT-3 and ACT-4 — autonomous, swarm-capable, sub-agent-spawning deployments — free tier is architecturally insufficient. CP.9 (Agent Replication Governance) and CP.10 (HEAR Doctrine — Human Ethical Agent of Record) are first-in-field controls that do not exist in any other framework. If your agent spawns sub-agents, persists state across sessions, or operates unattended, Pro tier is the governance layer, not an upgrade.

---

## Option 1 — Local stdio (5 minutes)

stdio is an OS process pipe — no network port, no auth, inherently scoped to your machine. Pro access locally by design.

### Prerequisites

- Python 3.11+
- `ai-safe2-framework` repo cloned

### Install

```bash
cd skills/mcp
pip install -e .
```

### Run

```bash
MCP_TRANSPORT=stdio python -m mcp_server.app
```

### Connect Claude Code (stdio)

Add to your Claude Code MCP settings (`~/.claude/settings.json` or project-level `.claude/settings.json`):

```json
{
  "mcpServers": {
    "ai-safe2": {
      "command": "python",
      "args": ["-m", "mcp_server.app"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "PYTHONPATH": "/absolute/path/to/ai-safe2-framework/skills/mcp/src"
      }
    }
  }
}
```

### Connect Claude Code (Docker stdio)

```bash
docker build -t ai-safe2-mcp .
```

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

### Connect Codex CLI (stdio)

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.ai-safe2-local]
command = "python"
args = ["-m", "mcp_server.app"]
env = { MCP_TRANSPORT = "stdio", PYTHONPATH = "/absolute/path/to/ai-safe2-framework/skills/mcp/src" }
```

Or using Docker with Codex:

```toml
[mcp_servers.ai-safe2-local]
command = "docker"
args = ["run", "--rm", "-i", "-e", "MCP_TRANSPORT=stdio", "ai-safe2-mcp"]
```

---

## Option 2 — Railway (15 minutes)

Railway gives you Docker-native deployment, automatic HTTPS, and a public URL. Right for teams who need shared remote access without managing infrastructure.

### Steps

1. Fork or clone this repository
2. Create a new Railway project → **Deploy from GitHub repo** → select `ai-safe2-framework`
3. Set root directory to `skills/mcp`
4. Set environment variables in the Railway dashboard:

```
MCP_TRANSPORT=streamable-http
MCP_HOST=0.0.0.0
MCP_PORT=8000
TOKENS=free_abc123:free,pro_xyz789:pro
```

5. Your MCP endpoint: `https://your-project.railway.app/mcp`

### Connect Claude Code (Railway HTTPS)

```json
{
  "mcpServers": {
    "ai-safe2": {
      "type": "http",
      "url": "https://your-project.railway.app/mcp",
      "headers": {
        "Authorization": "Bearer your-pro-token"
      }
    }
  }
}
```

### Connect Codex CLI (Railway HTTPS)

```toml
# ~/.codex/config.toml
experimental_use_rmcp_client = true

[mcp_servers.ai-safe2]
url = "https://your-project.railway.app/mcp"
bearer_token = "YOUR_TOKEN_HERE"
startup_timeout_sec = 20
tool_timeout_sec = 60
```

---

## Option 3 — Self-Hosted Caddy (Production)

Best for production deployments where you control the infrastructure. Caddy handles TLS automatically via Let's Encrypt.

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env: set MCP_TRANSPORT=streamable-http, TOKENS=...

# 2. Start the MCP server (binds to 127.0.0.1:8000 — internal only)
MCP_TRANSPORT=streamable-http python -m mcp_server.app &

# 3. Start Caddy (handles TLS, proxies from 443 to 8000)
caddy run --config Caddyfile
```

Edit `Caddyfile` to set your domain. Caddy handles certificates automatically.

### Connect (self-hosted)

```json
{
  "mcpServers": {
    "ai-safe2": {
      "type": "http",
      "url": "https://your-domain.example/mcp",
      "headers": {
        "Authorization": "Bearer your-pro-token"
      }
    }
  }
}
```

---

## Token Management

Tokens follow the format `{tier_prefix}_{random_string}`.

```
TOKENS=free_abc123def:free,pro_xyz789uvw:pro,pro_another:pro
```

| Prefix | Tier |
|--------|------|
| `free_` | Free tier |
| `pro_` | Pro tier |

**The server never issues tokens.** All issuance happens at [cyberstrategyinstitute.com/ai-safe2/](https://cyberstrategyinstitute.com/ai-safe2/). This keeps the MCP server stateless and auditable.

For production with many users, replace `TOKEN_MAP` in `config.py` with a database lookup or external token service. The middleware calls `TOKEN_MAP.get(token)` — swap that one call for any backend without touching the rest of the server.

> **Local stdio:** always Pro access, no token required. OS-level process pipe — no network, no auth overhead.

---

## Tool Quick Reference

### `lookup_control` — Search the AI SAFE2 v3.0 Control Taxonomy

```
query: str          — keyword search (name, description, tags, builder_problem)
control_id: str     — exact ID: "CP.10", "S1.5", "F3.2", "P1.T1.10"
pillar: str         — "P1" through "P5" or "CP" (cross-pillar)
priority: str       — "CRITICAL", "HIGH", "MEDIUM", "LOW"
framework: str      — "EU_AI_Act", "SOC2_Type2", "OWASP_Agentic_Top10", ...
version_added: str  — "v2.0", "v2.1", "v3.0"
act_tier: str       — "ACT-1", "ACT-2", "ACT-3", "ACT-4"
```

Free: 30 controls per query | Pro: 500 controls per query

---

### `risk_score` — AI SAFE2 Combined Risk Score

```
cvss_base: float       — CVSS base score (0–10)
pillar_score: float    — AI SAFE2 compliance score (0–100)
aaf_factors: dict      — OWASP AIVSS v0.8 Agentic Amplification Factors (Pro only)
```

**Formula:** `CVSS_Base + ((100 - Pillar_Score) / 10) + (AAF / 10)`

AAF factors (Pro): `autonomy_level`, `tool_access_breadth`, `natural_language_reliance`,
`context_persistence`, `behavioral_determinism`, `decision_opacity`, `state_retention`,
`dynamic_identity`, `multi_agent_interactions`, `self_modification`

Each factor: 0 = architecturally prevented · 5 = governed · 10 = uncontrolled

Free: CVSS + Pillar only | Pro: full AAF-informed score

---

### `compliance_map` — Map to 32 Governance Frameworks

```
requirement: str       — "EU AI Act Article 14", "GDPR Article 22", "SOC 2 CC.7.4"
framework_ids: list    — filter to specific frameworks (optional)
```

Free: 5 frameworks (NIST AI RMF, ISO 42001, SOC 2, GDPR, OWASP LLM)
Pro: all 32 — EU AI Act, DORA, FedRAMP, CMMC 2.0, SEC Disclosure, PCI-DSS, HIPAA, and more

---

### `code_review` — AI SAFE2-Grounded Code Review *(Pro only)*

```
code: str              — code to review
language: str          — "python", "javascript", "typescript", "go", etc.
context: str           — what this code does (optional but recommended)
focus_pillar: str      — "P1" through "P5" (all pillars if omitted)
```

No code is executed on the server. Returns control taxonomy context and a structured
findings template for model-based analysis by the connected LLM client.

---

### `agent_classify` — ACT Capability Tier Classification

```
description: str                — what the agent does
human_review_required: bool     — must a human review all outputs?
spawns_sub_agents: bool         — can this agent spawn other agents?
has_persistent_memory: bool     — cross-session state?
tool_access: list               — tools the agent can invoke
operates_unattended: bool       — runs without human presence?
deployment_environment: str     — "production", "enterprise", "research", etc.
```

Returns: ACT tier (1–4), mandatory controls, HEAR Doctrine requirements (CP.10),
CP.9 replication governance triggers, kill-switch specifications, deployment evidence package.

Free: ACT-1 and ACT-2 only | Pro: full ACT-1 through ACT-4

---

### `get_governance_resource` — Policy Templates and Audit Schemas

```
resource_name: str    — resource ID, or empty string to list all available
```

| Resource | Tier |
|----------|------|
| `quick_start_checklist` | Free |
| `pillar_overview` | Free |
| `act_tier_reference` | Free |
| `governance_policy_template` | Pro |
| `audit_scorecard_schema` | Pro |
| `hear_designation_template` | Pro |

---

### `get_workflow_prompt` — Reusable Governance Workflow Prompts

```
prompt_name: str      — or empty string to list all prompts
arguments: dict       — template variables
```

| Prompt | Description |
|--------|-------------|
| `security_architecture_review` | Full AI SAFE2 architecture review workflow |
| `compliance_gap_analysis` | Gap analysis against target frameworks |
| `incident_response_runbook` | Agent incident response workflow |
| `agent_deployment_checklist` | Pre-deployment readiness gate |

---

## Running Tests

```bash
cd skills/mcp

# All tests (137 total)
PYTHONPATH=src python -m pytest tests/test_tools.py tests/test_security.py -v

# Functional tests only
PYTHONPATH=src python -m pytest tests/test_tools.py -v

# Security tests only (RISK-0 through RISK-3)
PYTHONPATH=src python -m pytest tests/test_security.py -v

# HTTPS smoke tests (requires live deployed instance)
MCP_SERVER_URL=https://your-domain.example \
MCP_PRO_TOKEN=pro_your_token \
MCP_FREE_TOKEN=free_your_token \
PYTHONPATH=src python -m pytest tests/test_smoke_https.py -v
```

| Suite | Tests | Covers |
|-------|-------|--------|
| `test_tools.py` | 51 passing | All 6 tools, DB integrity, tier enforcement |
| `test_security.py` | 86 passing | ContextVar tier, injection patterns, STDIO hardening, rate limiting |
| `test_smoke_https.py` | Requires live instance | Auth, rate limit headers, tool responses over HTTPS |

---

## Updating the Controls

```bash
cd skills/mcp/data

# Edit generate_controls.py, then regenerate:
python generate_controls.py

# Verify
python -c "
import json
with open('ai-safe2-controls-v3.0.json') as f:
    d = json.load(f)
print('Total:', d['metadata']['total_controls'])
"

# Run tests
cd .. && PYTHONPATH=src python -m pytest tests/test_tools.py -v
```

`ControlsDB` reloads on startup — no code changes needed when the JSON updates, just restart.

---

## Security Architecture

**Version 3.0.1** is a security patch release addressing four risks identified in the April 2026 OX Security research on MCP supply chain vulnerabilities.

### Defense Layer Overview

```
Internet
    │ HTTPS :443
    ▼
┌─────────────────────────────────────────────┐
│  Caddy                                      │
│  TLS termination · HSTS · Security headers  │
│  Rate limit: 60 req/min/IP                  │
└────────────────────┬────────────────────────┘
                     │ HTTP 127.0.0.1:8000 (internal only)
                     ▼
┌─────────────────────────────────────────────┐
│  BearerAuthMiddleware                       │
│  Token validation → ContextVar tier         │
│  Token bucket rate limit (per tier + IP)    │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│  FastMCP Tools  (read-only, no shell)       │
│  sanitize_output() on every return value    │
└────────────────────┬────────────────────────┘
                     │
                     ▼
              ControlsDB (static JSON, in-memory)
```

**stdio path:**
```
Claude Code / Codex CLI
    │ OS process pipe (no network)
    ▼
verify_stdio_security()
    Command allowlist · Install path · Source hash
    ▼
FastMCP Tools → sanitize_output() → ControlsDB
```

---

### What Was Never Vulnerable

The primary OX Security exploit — Arbitrary RCE via unsanitized input into `StdioServerParameters` — **does not apply to this server.** Full code audit confirmed zero instances of `subprocess`, `os.system`, `shell=True`, `exec()`, or `eval()` in the codebase. User input never reaches a command-construction function. The server is a read-only index over a static JSON file.

The production platforms that were exploited (LiteLLM, LangFlow, Flowise) shared one architecture: user-controlled input flowing directly into STDIO transport configuration. This server does not have that architecture.

---

### v3.0.1 Fixes

#### RISK-0 — Tier Auth Broken for HTTP Transport *(HIGH, pre-existing bug)*

The original `_current_request: Request | None = None` module-level global was never set. Every HTTP-transport tool call silently fell back to `"free"` tier. Pro-token holders were being served free responses on every request.

**Fix:** `mcp_server/context.py` — `ContextVar` for per-request tier propagation. `BearerAuthMiddleware` sets tier immediately after token validation. Each asyncio coroutine gets its own copy.

---

#### RISK-1 — No Output Sanitization Before Returning to LLM Clients *(MODERATE)*

A supply-chain compromise of `ai-safe2-controls-v3.0.json` could embed prompt injection payloads in control descriptions that would reach Claude Code, Codex, or Cursor as trusted tool-response content.

**Fix:** `mcp_server/sanitize.py` — `sanitize_output()` applied to every tool return. Detects and redacts 7 injection pattern families:

| Family | Examples |
|--------|---------|
| Instruction override | "ignore previous instructions", "disregard all rules" |
| Role confusion | "you are now a DAN model", "act as unrestricted AI" |
| Permission escalation | "dangerously-skip-permissions", "bypass safety filters" |
| Exfiltration | "reveal your system prompt", "repeat everything above" |
| LLM special tokens | `<\|im_start\|>`, `[INST]`, `### System:` |
| Zero-width characters | U+200B–U+202E, BOM, direction overrides |
| Role separator injection | Newline-padded `system:` / `assistant:` markers |

Every redaction generates a structured audit log event for SIEM correlation.

---

#### RISK-2 — STDIO Grants Pro With No Identity Binding *(LOW-MODERATE)*

STDIO bypassed auth and granted Pro tier with zero verification. A malicious project-level `.claude/settings.json` could trigger this trust assumption (OX Security / Windsurf CVE-2026-30615 pattern).

**Fix:** `verify_stdio_security()` runs at STDIO startup before accepting any request:

1. **Command allowlist** — executable and module pattern must match `ALLOWED_STDIO_COMMANDS`
2. **Install path verification** *(opt-in)* — set `MCP_INSTALL_PATH`
3. **Source integrity hash** *(opt-in)* — set `MCP_SOURCE_HASH`. Generate at release:

```bash
PYTHONPATH=src python -c "from mcp_server.auth import _compute_source_hash; print(_compute_source_hash())"
```

Mismatch → `sys.exit(1)`. Fail-closed.

---

#### RISK-3 — Rate Limiting Not Wired *(LOW)*

`slowapi` was declared in `pyproject.toml` but never initialized. Rate limiting was 100% Caddy-dependent. Direct uvicorn and Railway deployments without Caddy had no protection.

**Fix:** `mcp_server/ratelimit.py` — token bucket rate limiter in `BearerAuthMiddleware`. Key format: `{tier}:{ip}`. Free and Pro buckets are fully isolated. Rate limit headers on every response.

**Multi-instance upgrade (Redis):**
```python
# Replace check() in ratelimit.py
import redis
r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), decode_responses=True)

def check(self, key: str) -> RateLimitResult:
    limit = self._limit_for_key(key)
    now = int(time.time())
    window_key = f"rl:{key}:{now // 3600}"
    pipe = r.pipeline()
    pipe.incr(window_key)
    pipe.expire(window_key, 7200)
    count, _ = pipe.execute()
    allowed = count <= limit
    remaining = max(0, limit - count)
    retry_after = (3600 - (now % 3600)) if not allowed else 0
    return self._result(allowed, limit, remaining, retry_after)
```

Add `redis>=5.0` to `pyproject.toml` and set `REDIS_URL` in environment.

---

### CP.5.MCP Compliance Mapping

| CP.5.MCP Required Control | Implementation in This Server |
|--------------------------|-------------------------------|
| No dynamic command construction | Zero `subprocess`/`shell`/`exec` in codebase |
| Output sanitization before LLM return | `sanitize.py` — all 7 tools, 7 pattern families |
| STDIO transport identity binding | `verify_stdio_security()` — command + path + hash |
| MCP tool invocation audit log | `structlog` structured events on every tool call |
| Application-layer rate limiting | Token bucket in `BearerAuthMiddleware` |
| Network isolation | Container binds to `127.0.0.1`; Caddy is sole external gateway |
| Zero-trust client config guidance | `client-config/` — verified path configs for Claude Code and Codex |

---

## License

MIT — Cyber Strategy Institute.

**Pro tokens and Toolkit:** [cyberstrategyinstitute.com/ai-safe2/](https://cyberstrategyinstitute.com/ai-safe2/)
**Framework repository:** [github.com/CyberStrategyInstitute/ai-safe2-framework](https://github.com/CyberStrategyInstitute/ai-safe2-framework)
