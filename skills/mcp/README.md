# AI SAFE2 v3.0 MCP Server
## Setup, Deployment, and Client Configuration

The AI SAFE2 MCP server exposes 7 tools, 2 MCP resources, and 2 MCP prompts
backed by the complete 161-control AI SAFE2 v3.0 taxonomy. It connects Claude Code,
Codex, and any MCP-compatible client to live control lookup, risk scoring, compliance
mapping, and governance resources.

**Two transports — both secure:**
- `stdio`: local use, inherently secure (OS process pipe), startup security verified
- `streamable-http` over HTTPS: remote access via Caddy TLS termination, bearer token auth + rate limiting

**Version 3.0.1** — Security patch release. See [Security Architecture](#security-architecture) for details.

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
| Rate limit | 30 req/hour | 1,000 req/hour |
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
docker build -t ai-safe2-mcp .
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

### Steps

1. Fork or clone the repository
2. Create a new Railway project → Deploy from GitHub repo
3. Set environment variables in Railway dashboard:
   ```
   MCP_TRANSPORT=streamable-http
   MCP_HOST=0.0.0.0
   MCP_PORT=8000
   TOKENS=free_yourtoken:free,pro_yourtoken:pro
   ```
4. Railway exposes HTTPS automatically. Your server URL will be:
   `https://your-project.railway.app/mcp`

### Connect Claude Code to Railway

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

---

## Option 3: Self-Hosted with Caddy (Production)

```bash
# Install Caddy
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
# ... (follow Caddy installation for your OS)

# Copy and edit .env
cp .env.example .env
# Edit .env: set MCP_TRANSPORT=streamable-http, TOKENS=...

# Run uvicorn (behind Caddy)
MCP_TRANSPORT=streamable-http python -m mcp_server.app &

# Run Caddy
caddy run --config Caddyfile
```

---

## Security Architecture

Version 3.0.1 addresses four security risks identified in the April 2026 OX Security
research on MCP supply chain vulnerabilities. The AI SAFE2 MCP server was already
substantially safer than affected platforms due to its read-only architecture and
absence of dynamic command construction. This release closes the remaining residual
exposures.

### What was never vulnerable (architecture-level)

The primary OX Security exploit — Arbitrary RCE via unsanitized input into
`StdioServerParameters` — does **not apply** to this server. A full code audit
confirmed zero instances of `subprocess`, `os.system`, `shell=True`, `exec()`,
or `eval()` anywhere in the codebase. User input never enters a command-construction
function. The server is a read-only index over a static JSON file.

### Fixes applied in v3.0.1

**RISK-0 (HIGH — pre-existing bug, not in OX research): Tier auth broken for HTTP transport**

The original code used `_current_request: Request | None = None` as a module-level
global that was never set. All HTTP-transport tool calls silently fell back to
`"free"` tier regardless of the authenticated token — Pro users were being served
free-tier responses.

Fix: `mcp_server/context.py` introduces a `contextvars.ContextVar` for tier
propagation. `BearerAuthMiddleware` calls `set_tier(tier)` after token validation.
Tool functions call `get_tier()` which reads from the ContextVar. Each asyncio
coroutine (request) gets its own ContextVar copy — no cross-request contamination.

**RISK-1 (MODERATE): No output sanitization before returning to LLM clients**

If `ai-safe2-controls-v3.0.json` is compromised (supply chain attack, malicious
PR merge), the server could return prompt injection payloads embedded in control
descriptions to Claude Code, Codex, or Cursor as trusted tool-response content.
The `code_review` tool was highest-risk as it directly injects control text as
LLM reasoning context.

Fix: `mcp_server/sanitize.py` implements `sanitize_output()` — a recursive
scanner that detects and redacts 7 injection pattern families:
instruction override, role confusion, permission escalation, system prompt
exfiltration, LLM special tokens, zero-width characters, and role separator injection.
All 7 tool functions in `app.py` wrap their return values with `sanitize_output()`.
Every redaction generates a structured audit log event (`sanitize.injection_detected`)
with pattern family, field path, and a truncated preview.

**RISK-2 (LOW-MODERATE): STDIO unconditionally grants Pro with no identity binding**

STDIO transport bypassed auth and granted Pro tier with zero verification.
Combined with OX Security's finding that zero-click IDE injection auto-executes
MCP servers from project-level configs (Windsurf CVE-2026-30615), a malicious
repo `.claude/settings.json` could trigger the STDIO trust bypass.

Fix: `verify_stdio_security()` in `mcp_server/auth.py` runs at STDIO startup
before any requests are accepted. Two checks:

1. **Command + module allowlist**: Verifies `sys.executable` is in `ALLOWED_STDIO_COMMANDS`
   and `sys.argv` matches an expected module pattern (e.g., `mcp_server.app`).
   Blocks a tampered settings.json that swaps `mcp_server.app` for a rogue module
   while still using a recognized Python binary.

2. **Source integrity hash** (opt-in): Set `MCP_SOURCE_HASH` in env to enable.
   On startup, SHA-256 of all `.py` files in the package + `ai-safe2-controls-v3.0.json`
   is computed and compared. Mismatch → `sys.exit(1)` (fail-closed).
   Generate hash at release: `PYTHONPATH=src python -c "from mcp_server.auth import _compute_source_hash; print(_compute_source_hash())"`

3. **Install path verification** (opt-in): Set `MCP_INSTALL_PATH`. Verifies
   `__file__` resolves inside the expected directory.

**Known limitation**: These checks cannot block a malicious settings.json that
points to a completely different binary (e.g., `command: /tmp/evil`). That threat
requires IDE-level MCP config signing (Claude Code roadmap) or OS-level process
isolation (Warden kernel containment). The server-side checks are defense-in-depth
for the case where the correct server binary is running but source has been tampered.

**RISK-3 (LOW): Rate limiting declared but not wired**

`slowapi` was listed in `pyproject.toml` but never imported or initialized in `app.py`.
Rate limiting was 100% Caddy-dependent. Direct uvicorn connections and Railway
deployments without Caddy had no application-layer rate limiting.

Fix: `mcp_server/ratelimit.py` implements a thread-safe token bucket rate limiter.
Applied inside `BearerAuthMiddleware` after tier resolution. Key format: `{tier}:{ip}`
— free and pro buckets are isolated. Rate limit state headers (`X-RateLimit-Limit`,
`X-RateLimit-Remaining`, `X-RateLimit-Window`, `Retry-After`) are attached to
every response.

### Multi-Instance Rate Limiting

The token bucket limiter uses in-process memory. This is correct for single-instance
deployments (single Railway dyno, single Docker container).

For multi-instance (horizontal scale), replace with a Redis-backed implementation:

```python
# In mcp_server/ratelimit.py — Redis upgrade
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
    return RateLimitResult(allowed, limit, remaining, retry_after,
                           self._build_headers(allowed, limit, remaining, retry_after))
```

Add `redis>=5.0` to `pyproject.toml` dependencies and set `REDIS_URL` in env.

### Enabling Source Integrity Verification (Recommended)

After deploying or updating the server:

```bash
# 1. Generate hash from your installed copy
PYTHONPATH=src python -c "from mcp_server.auth import _compute_source_hash; print(_compute_source_hash())"

# 2. Store in environment
echo "MCP_SOURCE_HASH=<hash-output>" >> .env

# 3. Restart server — startup will now verify source integrity
MCP_TRANSPORT=stdio python -m mcp_server.app
```

If the hash check fails on startup (hash mismatch detected), the server exits
immediately with code 1 and logs `auth.stdio_integrity_failure`. Do not ignore this.

---

## Available Tools

| Tool | Description | Tier |
|------|-------------|------|
| `lookup_control` | Search 161 controls by keyword, pillar, priority, framework, ACT tier, or ID | Free + Pro |
| `risk_score` | Calculate AI SAFE2 Combined Risk Score with optional OWASP AIVSS AAF | Free (basic) + Pro (full) |
| `compliance_map` | Map requirement to controls across up to 32 frameworks | Free (5 fw) + Pro (32 fw) |
| `code_review` | Return control taxonomy context for model-based code review | Pro only |
| `agent_classify` | Classify agent by ACT tier, return HEAR/CP.9 requirements | Free (ACT-1/2) + Pro (all) |
| `get_governance_resource` | Retrieve policy templates, audit schemas, checklists | Free (3) + Pro (all) |
| `get_workflow_prompt` | Get reusable AI SAFE2 workflow prompts | Free + Pro |

---

## Running Tests

```bash
# All tests (137 total: 51 functional + 86 security)
PYTHONPATH=src python -m pytest tests/ -v

# Security tests only
PYTHONPATH=src python -m pytest tests/test_security.py -v

# Functional tests only
PYTHONPATH=src python -m pytest tests/test_tools.py -v
```

Tests cover:
- ContextVar tier propagation and thread isolation (RISK-0)
- Injection pattern detection across all 7 families (RISK-1)
- Sanitization of nested dicts, lists, and edge cases (RISK-1)
- False positive validation against real control descriptions (RISK-1)
- Command allowlist and module pattern verification (RISK-2)
- Source hash computation, determinism, and tamper detection (RISK-2)
- Token bucket limits, tier isolation, refill, GC, and headers (RISK-3)
- End-to-end pipeline: middleware → ContextVar → tool → sanitize (all risks)
- Full 161-control data integrity and all original tool functionality (regression)

---

## Framework Mapping

The AI SAFE2 MCP server implements CP.5.MCP — the MCP Server Security Profile
added to AI SAFE2 v3.0 in response to the OX Security research. The seven
required controls are implemented as follows:

| CP.5.MCP Requirement | Implementation |
|---------------------|---------------|
| No dynamic command construction | Zero subprocess/shell/exec in codebase |
| Output sanitization before LLM return | `sanitize.py` — all 7 tools |
| STDIO transport identity binding | `verify_stdio_security()` — command + path + hash |
| MCP tool invocation audit log | `structlog` structured events on every tool call |
| Application-layer rate limiting | Token bucket in `BearerAuthMiddleware` |
| Network isolation | Container binds to 127.0.0.1; Caddy handles external TLS |
| Zero-trust client config guidance | `client-config/` examples use verified paths |

---

## License

MIT — Cyber Strategy Institute. Use freely. Attribute appropriately.
Tokens at **cyberstrategyinstitute.com/ai-safe2/**
