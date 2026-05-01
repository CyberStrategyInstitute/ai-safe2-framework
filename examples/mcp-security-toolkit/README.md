# AI SAFE2 MCP Security Toolkit

> **Score. Scan. Wrap. Any MCP server. In minutes.**
> AI SAFE2 v3.0 CP.5.MCP — open-source, 134 tests passing.

[![AI SAFE2](https://img.shields.io/badge/AI_SAFE2-v3.0-orange)](https://cyberstrategyinstitute.com/ai-safe2/)
[![Tests](https://img.shields.io/badge/Tests-134_passing-brightgreen)]()
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey)]()

---

The OX Security April 2026 disclosure documented RCE across 200,000 MCP server instances via a structural flaw Anthropic classified as expected behavior. The full MCP threat surface is larger than the headlines reported — billing amplification, persistent memory injection, multi-agent lateral movement, rug pull attacks, and Swarm C2.

This toolkit implements AI SAFE2 v3.0 CP.5.MCP as three composable tools:

| Tool | What it does | Who uses it |
|------|-------------|-------------|
| `mcp-score` | Remote black-box CP.5.MCP assessment | Anyone connecting to an MCP server |
| `mcp-scan` | Static code analysis across 20 finding classes | MCP server builders |
| `mcp-safe-wrap` | Drop-in injection scanning and audit proxy | Anyone consuming an MCP server |

All three ship as a single package. One install.

```bash
pip install aisafe2-mcp-tools
```

---

## Quick Start

### Score any MCP server (30 seconds)
```bash
mcp-score https://your-mcp-server.example/mcp
mcp-score https://your-mcp-server.example/mcp --token pro_xyz789
```

### Scan your server's source code
```bash
mcp-scan /path/to/your/server
mcp-scan . --output json > report.json
mcp-scan . --output html > report.html
mcp-scan . --ci --severity critical   # Exit 1 if critical findings
```

### Wrap a local server (STDIO mode)
```bash
# Intercept and scan the OS pipe between your AI client and the server
mcp-safe-wrap stdio -- python -m mcp_server.app
mcp-safe-wrap stdio -- node dist/server.js
```

### Wrap a remote server (HTTP proxy mode)
```bash
# Run a local scanning proxy for any HTTP MCP server
mcp-safe-wrap proxy https://external-mcp.example/mcp --token your-token
# Then connect Claude Code to: http://localhost:8080/proxy
```

---

## mcp-score

Runs a remote black-box assessment against any MCP HTTP server. No source code access required.

**What it checks:**

| Check | Max Points | What it detects |
|-------|-----------|----------------|
| Authentication | 25 | OAuth 2.1, bearer, none |
| TLS | 15 | HTTPS, plain HTTP |
| Tool injection scan | 20 | 28 injection families in tool schemas |
| FSP scan | 10 | CyberArk Full Schema Poisoning patterns |
| Security headers | 10 | HSTS, X-Frame, X-Content-Type, Referrer |
| Rate limiting | 10 | Application-layer (not just Caddy) |
| Session ID in URL | 5 | CVE-2025-6515 pattern |
| SSRF surface | 5 | URL-accepting parameters |
| Builder attestation | +25 | Controls not verifiable remotely |

**Score thresholds:**

| Score | Rating | Badge eligible |
|-------|--------|---------------|
| 90–100 | Secure | Yes |
| 70–89 | Acceptable | Yes |
| 50–69 | Elevated Risk | No |
| 30–49 | High Risk | No |
| 0–29 | Critical | No |

**Output formats:**
```bash
mcp-score https://server.example/mcp                    # Terminal (default)
mcp-score https://server.example/mcp --output json      # Machine-readable
mcp-score https://server.example/mcp --output html > r.html
mcp-score servers.txt --batch --output json             # Multiple servers
```

**CI/CD integration:**
```bash
# Exit 1 if score drops below threshold
mcp-score https://server.example/mcp --ci-fail-below 70
```

### Builder Attestation

Controls that cannot be verified remotely (like `shell=True` in source code) can be attested via `/.well-known/mcp-security.json`. This file is publicly readable (no auth) and adds up to +25 bonus points.

Create at your server root:
```json
{
  "mcp_security_version": "1.0",
  "framework": "AI SAFE2 v3.0 CP.5.MCP",
  "server_name": "your-server-name",
  "controls": {
    "MCP-1_no_dynamic_commands": true,
    "MCP-2_output_sanitization": "aisafe2-mcp-tools>=1.0.0",
    "MCP-4_source_hash": "your-computed-hash-here",
    "MCP-5_audit_logging": true,
    "MCP-6_network_isolation": "127.0.0.1 only"
  },
  "source_code": "https://github.com/your-org/your-server",
  "contact": "security@your-org.example"
}
```

Generate your source hash:
```bash
# From your server root
PYTHONPATH=src python -c "
import hashlib
from pathlib import Path
h = hashlib.sha256()
for f in sorted(Path('src').rglob('*.py')):
    h.update(f.name.encode()); h.update(f.read_bytes())
print(h.hexdigest())
"
```

---

## mcp-scan

Static code analysis across the full CVE taxonomy from the CSI MCP Threat Intelligence Report.

**Finding classes:**

| Class | Finding IDs | What it catches |
|-------|------------|-----------------|
| **Critical — RCE** | RCE-001 through RCE-006 | Dynamic StdioServerParameters (OX finding), shell=True, eval(), unsafe yaml.load(), path traversal, kubectl injection |
| **High — Injection** | INJ-001 through INJ-005 | Missing output sanitization, SSRF-enabling URL params, OAuth forwarding, rug pull exposure |
| **High — Security** | SEC-001 through SEC-006 | 0.0.0.0 binding, session URL exposure, OAuth confused deputy, cross-tenant isolation |
| **Medium — Operational** | RL-001, RL-002, LOG-001, LOG-002, MEM-001 | Rate limiting gaps, LLM API cost limits, missing audit logs, persistent memory |
| **Low — Hygiene** | AUTH-001, DEP-001, DEP-002, CONF-001 | STDIO verify missing, unpinned deps, vulnerable dep versions, hardcoded creds |

**Dependency CVE checking:**
```bash
# Checks pyproject.toml and requirements.txt against known-vulnerable MCP packages
mcp-scan . --deps-only
```

**Auto-fix (HIGH and below only — critical never auto-fixed):**
```bash
mcp-scan fix --interactive    # Step through findings with guidance
mcp-scan fix --auto           # Apply safe auto-fixes
```

**Fix templates** are in `src/aisafe2_mcp_tools/scan/fixes/` — one per critical finding ID.

---

## mcp-safe-wrap

Drop-in consumer-side protection. No server code changes required.

### STDIO mode

Wraps any local server process. Intercepts the OS pipe in both directions.

```bash
# Direct use
mcp-safe-wrap stdio -- python -m mcp_server.app

# Log-only mode (no blocking — observe what would be blocked)
mcp-safe-wrap stdio --log-only -- python -m mcp_server.app

# With audit log
mcp-safe-wrap stdio --audit-log ./audit.jsonl -- python -m mcp_server.app
```

**Claude Code config** (`~/.claude/settings.json` or `.claude/settings.json`):
```json
{
  "mcpServers": {
    "safe-server": {
      "command": "mcp-safe-wrap",
      "args": ["stdio", "--", "python", "-m", "mcp_server.app"],
      "env": {"PYTHONPATH": "/path/to/src"}
    }
  }
}
```

### HTTP proxy mode

Runs a local Starlette proxy on `127.0.0.1:8080`. Connect Claude Code to the proxy URL instead of the remote server.

```bash
# Basic
mcp-safe-wrap proxy https://external-mcp.example/mcp --token your-token

# Full options
mcp-safe-wrap proxy https://external-mcp.example/mcp \
  --token your-token \
  --local-port 8080 \
  --rate-limit 200 \
  --audit-log ~/.mcp-safe-wrap/audit.jsonl

# Disable input scanning (outputs still scanned)
mcp-safe-wrap proxy https://example.com/mcp --no-scan-inputs
```

**Claude Code config** (proxy mode):
```json
{
  "mcpServers": {
    "safe-external": {
      "type": "http",
      "url": "http://localhost:8080/proxy"
    }
  }
}
```

**What it scans:**
- Tool descriptions and schemas: 28 injection pattern families
- Tool response bodies: ATPA steering language, role injection, exfiltration patterns
- URL parameters: SSRF blocklist (AWS IMDS, RFC 1918, loopback, file://)

**Wire format guarantee:** When scanning is disabled (`--no-scan-inputs` or `--no-scan-outputs`), original bytes are passed through unchanged. No JSON re-serialization occurs.

**Audit log format** (JSONL, append-only):
```json
{"event": "tool_invocation", "method": "tools/call", "tool_name": "search", "client_ip": "127.0.0.1", "timestamp": "2026-04-27T..."}
{"event": "output_injection_detected", "finding_count": 2, "families": ["instruction_override"], "timestamp": "..."}
```

---

## Earning the AI SAFE2 MCP Badge

**Step 1:** Fix findings from `mcp-scan`

**Step 2:** Deploy with security controls, add `.well-known/mcp-security.json`

**Step 3:** Score your server
```bash
mcp-score https://your-server.example/mcp --badge
```

**Step 4:** Add badge to README (output by `--badge` flag when eligible)
```markdown
[![AI SAFE2 MCP Score: 85/100](https://img.shields.io/badge/AI%20SAFE2%20MCP-Score%3A%2085%2F100-orange?style=for-the-badge)](https://cyberstrategyinstitute.com/ai-safe2/mcp-verify?url=https%3A%2F%2Fyour-server.example%2Fmcp)
```

The badge links to the CSI verification page. Anyone can click it and re-run `mcp-score` to verify the score independently. It is not a self-reported claim.

**Badge validity:** 90 days. Re-scan required after any update affecting scored controls.

---

## Architecture

```
shared/
  patterns.py        28-family injection library + SSRF blocklist
                     Single source of truth for all three tools

score/
  assessor.py        Assessment coordinator
  auth_checker.py    MCP-7: authentication posture
  schema_scanner.py  MCP-2: injection + FSP scan
  header_checker.py  MCP-6: security response headers
  ssrf_detector.py   MCP-6: SSRF surface detection
  scorer.py          Scoring rubric + rating thresholds
  badge.py           Badge generation + .well-known spec
  reporter.py        Terminal / JSON / HTML output
  models.py          CheckResult, AttestationData, ScoreReport

scan/
  analyzer.py        Scan coordinator
  ast_analyzer.py    AST-based RCE-001 detection
  pattern_scanner.py Regex checks (RCE-002 through CONF-001)
  dep_checker.py     Dependency CVE verification
  findings.py        Finding data model + stable IDs
  reporter.py        Terminal / JSON / HTML output
  fixes/             Fix templates per critical finding ID

wrap/
  wrapper.py         STDIO wrapper coordinator
  proxy.py           HTTP proxy implementation
  scanner.py         Message injection + SSRF scanning
  audit.py           JSONL audit log writer
  ratelimit.py       SyncTokenBucket + AsyncTokenBucket
```

---

## Running Tests

```bash
# All 134 tests
PYTHONPATH=src python -m pytest tests/ -v

# Unit tests only (112 tests)
PYTHONPATH=src python -m pytest tests/test_toolkit.py -v

# System integration tests (22 tests — validates tools work as a system)
PYTHONPATH=src python -m pytest tests/test_integration.py -v
```

The integration tests validate the three tools as a **system**: that scan findings map to patterns blocked at runtime by mcp-safe-wrap, that score results accurately reflect server posture, and that the shared pattern library is consistent across all three tools.

---

## CP.5.MCP Compliance Map

| Tool | MCP-1 | MCP-2 | MCP-3 | MCP-4 | MCP-5 | MCP-6 | MCP-7 |
|------|-------|-------|-------|-------|-------|-------|-------|
| mcp-scan | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| mcp-score | — | ✓ | — | ✓ | — | ✓ | ✓ |
| mcp-safe-wrap | — | ✓ | — | — | ✓ | ✓ | — |

Use all three together for full CP.5.MCP coverage.

The full CP.5.MCP specification including MCP-8 through MCP-13 (billing amplification, context-tool isolation, multi-agent provenance, schema temporal profiling, Swarm C2 detection, failure taxonomy) is in [`../../00-cross-pillar/CP.5.MCP-updated.md`](../../00-cross-pillar/CP.5.MCP-updated.md).

---

## Reference Implementation

The AI SAFE2 MCP Server (v3.0.1) is the reference implementation of CP.5.MCP. It demonstrates all seven controls in a production-deployable server:

[`../../skills/mcp/`](../../skills/mcp/) — 161 controls, 32 frameworks, 137 tests passing.

---

**AI SAFE2 Framework:** [github.com/CyberStrategyInstitute/ai-safe2-framework](https://github.com/CyberStrategyInstitute/ai-safe2-framework)

**Pro tokens and Toolkit:** [cyberstrategyinstitute.com/ai-safe2/](https://cyberstrategyinstitute.com/ai-safe2/)

**License:** MIT — Cyber Strategy Institute
