# AI SAFE2 MCP Security Toolkit

> **Score. Scan. Wrap. Any MCP server. In minutes.**
> AI SAFE2 v3.0 CP.5.MCP — open-source, 195 tests passing.

[![AI SAFE2](https://img.shields.io/badge/AI_SAFE2-v3.0-orange)](https://cyberstrategyinstitute.com/ai-safe2/)
[![Tests](https://img.shields.io/badge/Tests-195_passing-brightgreen)]()
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey)]()

---

## Navigation

[Overview](#overview) &nbsp;|&nbsp;
[Quick Start](#quick-start) &nbsp;|&nbsp;
[mcp-score](#mcp-score) &nbsp;|&nbsp;
[mcp-scan](#mcp-scan) &nbsp;|&nbsp;
[mcp-safe-wrap](#mcp-safe-wrap) &nbsp;|&nbsp;
[CP.5.MCP Compliance Map](#cp5mcp-compliance-map) &nbsp;|&nbsp;
[Earning the Badge](#earning-the-ai-safe2-mcp-badge) &nbsp;|&nbsp;
[Architecture](#architecture) &nbsp;|&nbsp;
[Running Tests](#running-tests) &nbsp;|&nbsp;
[Reference Implementation](#reference-implementation)

---

## Overview

The OX Security April 2026 disclosure documented RCE across 200,000 MCP server instances via a structural flaw Anthropic classified as expected behavior. The full MCP threat surface is larger than the headlines reported — billing amplification, persistent memory injection, multi-agent lateral movement, rug pull attacks, and Swarm C2.

This toolkit implements AI SAFE2 v3.0 CP.5.MCP as three composable tools:

| Tool | What it does | Who uses it |
|------|-------------|-------------|
| `mcp-score` | Remote black-box CP.5.MCP assessment | Anyone connecting to an MCP server |
| `mcp-scan` | Static code analysis across 23 finding classes | MCP server builders |
| `mcp-safe-wrap` | Drop-in injection scanning, schema pinning, and audit proxy | Anyone consuming an MCP server |

All three ship as a single package. One install.

```bash
pip install aisafe2-mcp-tools
```

[↑ Navigation](#navigation)

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
mcp-safe-wrap stdio -- python -m mcp_server.app
mcp-safe-wrap stdio -- node dist/server.js
```

### Wrap a remote server (HTTP proxy mode)
```bash
# Injection scanning + schema pinning (MCP-11)
mcp-safe-wrap proxy https://external-mcp.example/mcp --token your-token --pin-schema
# Then connect Claude Code to: http://localhost:8080/proxy
```

[↑ Navigation](#navigation)

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
mcp-score https://server.example/mcp --ci-fail-below 70
```

### Builder Attestation

Controls that cannot be verified remotely (like `shell=True` in source code) can be attested via `/.well-known/mcp-security.json`. This file is publicly readable (no auth) and adds up to +25 bonus points.

The bonus is risk-weighted across all 11 attested CP.5.MCP controls. Servers that only attest the original five controls (MCP-1/2/4/5/6) earn 13 of 25 — full bonus requires attesting MCP-8 through MCP-13.

| Attested Field | MCP Control | Points | Risk Basis |
|---|---|:---:|---|
| `no_dynamic_commands` | MCP-1 | 5 | OX Security confirmed RCE |
| `context_tool_isolation` | MCP-9 | 4 | MCP-UPD 92.9% attack surface |
| `output_sanitization` | MCP-2 | 3 | Core injection defense |
| `session_economics` | MCP-8 | 3 | $47K confirmed, 658x amplification |
| `schema_temporal_profiling` | MCP-11 | 2 | Rug pull — delayed_weeks profile |
| `source_hash` | MCP-4 | 2 | Post-install tamper detection |
| `audit_logging` | MCP-5 | 2 | Forensic foundation |
| `multi_agent_provenance` | MCP-10 | 1 | Lateral movement via delegation |
| `network_isolation` | MCP-6 | 1 | Egress control |
| `swarm_c2_controls` | MCP-12 | 1 | Swarm C2 detection |
| `failure_taxonomy` | MCP-13 | 1 | CP.1 taxonomy correctness |
| **Total** | | **25** | |

Create at your server root:
```json
{
  "mcp_security_version": "2.0",
  "framework": "AI SAFE2 v3.0 CP.5.MCP",
  "server_name": "your-server-name",
  "controls": {
    "MCP-1_no_dynamic_commands": true,
    "MCP-2_output_sanitization": "aisafe2-mcp-tools>=1.0.0",
    "MCP-4_source_hash": "your-computed-hash-here",
    "MCP-5_audit_logging": true,
    "MCP-6_network_isolation": "127.0.0.1 only",
    "MCP-8_session_economics": true,
    "MCP-9_context_tool_isolation": "aisafe2-mcp-tools>=1.0.0",
    "MCP-10_multi_agent_provenance": false,
    "MCP-11_schema_temporal_profiling": true,
    "MCP-12_swarm_c2_controls": false,
    "MCP-13_failure_taxonomy": true
  },
  "source_code": "https://github.com/your-org/your-server",
  "contact": "security@your-org.example"
}
```

Generate your source hash:
```bash
PYTHONPATH=src python -c "
import hashlib
from pathlib import Path
h = hashlib.sha256()
for f in sorted(Path('src').rglob('*.py')):
    h.update(f.name.encode()); h.update(f.read_bytes())
print(h.hexdigest())
"
```

A complete `.well-known/mcp-security.json` template with all 13 control fields is in [`examples/mcp-security.json`](examples/mcp-security.json).

[↑ Navigation](#navigation)

---

## mcp-scan

Static code analysis across the full CVE taxonomy from the CSI MCP Threat Intelligence Report.

**Finding classes:**

| Class | Finding IDs | CP.5.MCP | What it catches |
|-------|------------|----------|-----------------|
| **Critical — RCE** | RCE-001 through RCE-006 | MCP-1 | Dynamic StdioServerParameters (OX finding), shell=True, eval(), unsafe yaml.load(), path traversal, kubectl injection |
| **High — Injection** | INJ-001 through INJ-005 | MCP-2 | Missing output sanitization, SSRF-enabling URL params, OAuth forwarding, rug pull exposure |
| **High — Security** | SEC-001 through SEC-006 | MCP-4 | 0.0.0.0 binding, session URL exposure, OAuth confused deputy, cross-tenant isolation |
| **Medium — Rate/Cost** | RL-001 | MCP-6 | Rate limiting gaps |
| **Medium — Economics** | RL-002 | MCP-8 | LLM API cost limits absent (billing amplification risk) |
| **Medium — Logging** | LOG-001, LOG-002 | MCP-5 | Missing audit logs |
| **Medium — Provenance** | MEM-001 | MCP-10 | Persistent memory without isolation or expiry |
| **Medium — Context** | CTI-001 | MCP-9 | Unguarded retrieval-to-disclosure chains (MCP-UPD risk) |
| **Medium — Schema** | STP-001 | MCP-11 | tools/list calls without hash pinning (rug pull risk) |
| **Medium — Swarm** | SWM-001 | MCP-12 | Multi-agent orchestration without topology monitoring |
| **Low — Hygiene** | AUTH-001, DEP-001, DEP-002, CONF-001 | MCP-3/4 | STDIO verify missing, unpinned deps, vulnerable dep versions, hardcoded creds |

**Dependency CVE checking:**
```bash
mcp-scan . --deps-only
```

**Auto-fix (HIGH and below only — critical never auto-fixed):**
```bash
mcp-scan fix --interactive
mcp-scan fix --auto
```

Fix templates are in `src/aisafe2_mcp_tools/scan/fixes/`.

[↑ Navigation](#navigation)

---

## mcp-safe-wrap

Drop-in consumer-side protection. No server code changes required.

### STDIO mode

```bash
mcp-safe-wrap stdio -- python -m mcp_server.app
mcp-safe-wrap stdio --log-only -- python -m mcp_server.app
mcp-safe-wrap stdio --audit-log ./audit.jsonl -- python -m mcp_server.app
```

**Claude Code config** (`~/.claude/settings.json`):
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

```bash
# Basic
mcp-safe-wrap proxy https://external-mcp.example/mcp --token your-token

# With schema pinning (MCP-11) and audit log
mcp-safe-wrap proxy https://external-mcp.example/mcp \
  --token your-token \
  --pin-schema \
  --audit-log ~/.mcp-safe-wrap/audit.jsonl \
  --rate-limit 200
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

**Schema pinning (`--pin-schema`, MCP-11):** Records the `tools/list` response hash at first connection. Alerts and writes an audit event with CP.1 taxonomy `delayed_weeks` classification on any subsequent hash change not accompanied by a documented release event. Implements the rug pull detection requirement from AI SAFE2 v3.0 CP.5.MCP-11.

**Audit log format** (JSONL, append-only):
```json
{"event": "tool_invocation", "method": "tools/call", "tool_name": "search", "timestamp": "..."}
{"event": "output_injection_detected", "finding_count": 2, "families": ["instruction_override"], "cp1_cognitive_surface": "model", "cp1_memory_persistence": "session", "timestamp": "..."}
{"event": "schema_changed", "baseline_hash": "abc123...", "current_hash": "def456...", "cp1_cognitive_surface": "model", "cp1_memory_persistence": "delayed_weeks", "action": "ALERT — schema change without documented release event", "timestamp": "..."}
```

All audit events for injection-class and schema-mutation events are enriched with CP.1 taxonomy tags (`cp1_cognitive_surface`, `cp1_memory_persistence`) per AI SAFE2 v3.0 CP.5.MCP-13.

**Wire format guarantee:** When scanning is disabled (`--no-scan-inputs` or `--no-scan-outputs`), original bytes are passed through unchanged.

[↑ Navigation](#navigation)

---

## CP.5.MCP Compliance Map

The toolkit provides verifiable coverage for 10 of the 13 CP.5.MCP controls. MCP-10, MCP-12 (full), and MCP-8 (runtime enforcement) require orchestrator-level integration beyond the scope of a static analysis and proxy tool.

| Control | mcp-scan | mcp-score | mcp-safe-wrap | Notes |
|---------|:--------:|:---------:|:-------------:|-------|
| MCP-1 No Dynamic Commands | ✓ | -- | -- | RCE-001 through RCE-006 |
| MCP-2 Output Sanitization | ✓ | ✓ | ✓ | INJ-001 through INJ-005; runtime scanning |
| MCP-3 Registry Provenance | ✓ | -- | -- | DEP-001, DEP-002 |
| MCP-4 STDIO Integrity | ✓ | ✓ | -- | SEC-001 through SEC-006; attestation |
| MCP-5 Tool Audit Log | ✓ | -- | ✓ | LOG-001; immutable JSONL audit |
| MCP-6 Network Isolation | ✓ | ✓ | ✓ | RL-001; SSRF blocklist |
| MCP-7 Zero-Trust Config | -- | ✓ | ✓ | Auth assessment; proxy wrapping |
| MCP-8 Session Economics | ~ | -- | -- | RL-002 flags risk; runtime budgets require orchestrator |
| MCP-9 Context-Tool Isolation | ✓ | -- | ✓ | CTI-001; runtime sanitize_value() on all external data |
| MCP-10 Delegation Edge | ~ | -- | -- | MEM-001 flags persistent memory; lineage tokens require CP.9 orchestrator |
| MCP-11 Schema Temporal | ✓ | -- | ✓ | STP-001; --pin-schema hash comparison |
| MCP-12 Swarm C2 | ~ | -- | -- | SWM-001 flags multi-agent code; topology monitoring requires orchestrator |
| MCP-13 Failure Taxonomy | -- | -- | ✓ | CP.1 tags auto-injected into all audit events |

`✓` = implemented | `~` = detection/flagging only | `--` = out of scope for this tool layer

Use all three together for full coverage across the controls this tool layer can address. MCP-10, MCP-12 (full behavioral), and MCP-8 runtime enforcement require deployment at the CP.4 Agentic Control Plane or CP.9 ARG layer.

Full CP.5.MCP control specifications: [`../../00-cross-pillar/MCP.md`](../../00-cross-pillar/MCP.md)

[↑ Navigation](#navigation)

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

The badge links to the CSI verification page. Anyone can click it and re-run `mcp-score` to verify the score independently.

**Badge validity:** 90 days. Re-scan required after any update affecting scored controls.

[↑ Navigation](#navigation)

---

## Architecture

```
shared/
  patterns.py        28-family injection library + SSRF blocklist
                     Single source of truth for MCP-2 and MCP-9 across all three tools

score/
  assessor.py        Assessment coordinator + attestation parser (MCP-1 through MCP-13)
  auth_checker.py    MCP-7: authentication posture
  schema_scanner.py  MCP-2: injection + FSP scan
  header_checker.py  MCP-6: security response headers
  ssrf_detector.py   MCP-6: SSRF surface detection
  scorer.py          Scoring rubric + rating thresholds + attestation bonus
  badge.py           Badge generation + .well-known spec (13-control template)
  reporter.py        Terminal / JSON / HTML output
  models.py          CheckResult, AttestationData (MCP-1 through MCP-13), ScoreReport

scan/
  analyzer.py        Scan coordinator
  ast_analyzer.py    AST-based RCE-001 detection
  pattern_scanner.py Regex checks (RCE-002 through SWM-001 — 23 finding classes)
  dep_checker.py     Dependency CVE verification
  findings.py        Finding data model + stable IDs + control map (MCP-1 through MCP-13)
  reporter.py        Terminal / JSON / HTML output
  fixes/             Fix templates per critical finding ID

wrap/
  wrapper.py         STDIO wrapper coordinator
  proxy.py           HTTP proxy + schema pinning (MCP-11)
  scanner.py         Message injection + SSRF scanning (MCP-2, MCP-6, MCP-9)
  audit.py           JSONL audit log + CP.1 taxonomy enrichment (MCP-5, MCP-13)
  ratelimit.py       SyncTokenBucket + AsyncTokenBucket
```

[↑ Navigation](#navigation)

---

## Running Tests

```bash
# All 160 tests
PYTHONPATH=src python -m pytest tests/ -v

# Unit tests (132 tests)
PYTHONPATH=src python -m pytest tests/test_toolkit.py -v

# Integration tests (28 tests)
PYTHONPATH=src python -m pytest tests/test_integration.py -v

# MCP-8 through MCP-13 controls only
PYTHONPATH=src python -m pytest tests/ -k "MCP8 or MCP9 or MCP10 or MCP11 or MCP12 or MCP13" -v
```

The integration tests validate the three tools as a **system**: that scan findings map to patterns blocked at runtime by mcp-safe-wrap, that score results accurately reflect server posture, that the shared pattern library is consistent across all three tools, and that MCP-8 through MCP-13 controls work end-to-end.

[↑ Navigation](#navigation)

---

## Reference Implementation

The AI SAFE2 MCP Server (v3.0.1) is the reference implementation of CP.5.MCP. It demonstrates all 13 controls in a production-deployable server:

[`../../skills/mcp/`](../../skills/mcp/) — 161 controls, 32 frameworks, 137 tests passing.

---

**AI SAFE2 Framework:** [github.com/CyberStrategyInstitute/ai-safe2-framework](https://github.com/CyberStrategyInstitute/ai-safe2-framework)

**Full CP.5.MCP Specification:** [00-cross-pillar/MCP.md](../../00-cross-pillar/MCP.md)

**Pro tokens and Toolkit:** [cyberstrategyinstitute.com/ai-safe2/](https://cyberstrategyinstitute.com/ai-safe2/)

**License:** MIT — Cyber Strategy Institute

**Full CP.5.MCP Specification:** [00-cross-pillar/MCP.md](../../00-cross-pillar/MCP.md)

**Pro tokens and Toolkit:** [cyberstrategyinstitute.com/ai-safe2/](https://cyberstrategyinstitute.com/ai-safe2/)

**License:** MIT — Cyber Strategy Institute
