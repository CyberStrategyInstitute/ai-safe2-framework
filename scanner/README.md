# AI SAFE² Scanner
### Pre-commit and CI analysis for agentic AI codebases

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Surface](https://img.shields.io/badge/Surface-Scanner-820F1A?style=flat-square)](./README.md)
[![Rules](https://img.shields.io/badge/Rules-52-808080?style=flat-square)](./rules/)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

**Previous:** [← NEXUS](../NEXUS/) | **Next:** [Gateway / Runtime Enforcement →](../gateway/)

---

## Role in the v3.1 Stack

| Surface | Tool | When |
|---|---|---|
| **Design-time** | Skills + AI SAFE² MCP Server | While designing and building |
| **Pre-commit / CI** | **Scanner, you are here** | Before code reaches production |
| **Runtime** | Gateway / enforcement components | During execution |

The scanner evaluates code and configuration against AI SAFE² patterns. It is a static-analysis aid, not proof of full control conformance.

---

## v3.1 Rule Model

AI SAFE² v3.1 keeps the **161-control core framework taxonomy** and adds a machine-readable **CP.5.MCP profile with MCP-1 through MCP-19**.

The scanner currently exposes **52 detection rules**:

- 40 existing pillar and cross-pillar rules;
- 12 grouped CP.5.MCP rules that cover the highest-value static indicators across MCP-1 through MCP-19.

Profile rules are grouped because several MCP controls require runtime evidence and cannot be proven by a one-pattern-per-control static check.

### Important v3.1 guarantees

- `server/discover` is optional under MCP `2026-07-28`; the scanner does **not** require it.
- Legacy `Mcp-Session-Id` must not be treated as identity or the authorization boundary.
- MCP-19 intended-resource/audience and SSRF findings are **advisory (`INFO`)** until deployment-specific authorization behavior can be proven.
- Profile findings do not increase the 161 core framework count.

---

## What the Scanner Detects

| Category | Representative controls |
|---|---|
| Secrets and NHI | P1, CP.4, MCP-9 |
| Injection and untrusted content | P1, S1.6, MCP-2 |
| Memory and persistence governance | S1.5, A2.6, MCP-12/MCP-16 |
| Unsafe execution | P1.T2.1, MCP-1 |
| Server and binary provenance | P1.T1.9, MCP-3/MCP-4 |
| Audit gaps | A2.5, P4.T8.3, MCP-5 |
| Tool input validation | P1.T1.1, MCP-6 |
| Trust establishment | CP.4, MCP-7 |
| Economic ceilings | F3.2, MCP-8 |
| Delegation lineage | CP.9, MCP-10 |
| Catalog/schema drift | A2.6, MCP-11/MCP-18 |
| Protocol assertion/replay integrity | MCP-15/MCP-17 |
| Authorization-chain integrity | MCP-19, advisory |
| Missing HEAR / CRT | CP.10, CP.8 |
| Agent spawning | CP.9 |

---

## Quick Start

```bash
pip install -r scanner/requirements.txt

# Scan current directory
python -m scanner.cli scan .

# Scan with a tier threshold
python -m scanner.cli scan ./my-agent --tier Tier2

# JSON and SARIF report
python -m scanner.cli scan . --report both --output report.json

# Fail CI when score is below threshold
python -m scanner.cli scan . --fail-under 80
```

---

## Output

**Score:** static-analysis score derived from finding severity.

**ACT estimate:** inferred autonomy signals used to surface governance gaps such as HEAR, CRT, and replication governance.

**Governance gaps:** structural indications that required ownership, logging, fail-safe, delegation, or protocol controls may be absent.

**Framework mappings:** findings are enriched from the core control taxonomy when data is available. MCP profile metadata is maintained separately from the 161 core controls.

Static findings are evidence inputs. They are not a substitute for runtime conformance testing.

---

## MCP Profile Rules

The v3.1 MCP rules live at:

[`scanner/rules/mcp_profile.py`](./rules/mcp_profile.py)

The machine-readable profile they correspond to is:

[`skills/mcp/data/mcp-profile-v3.1.json`](../skills/mcp/data/mcp-profile-v3.1.json)

The canonical normative specification is:

[CP.5.MCP v3.1](../00-cross-pillar/cp5_mcp_server_security.md)

Regression tests enforce:

- 52 total rules;
- 12 MCP profile rules;
- MCP-19 remains advisory;
- no `server/discover` presence rule;
- coverage reaches the new MCP-16/MCP-18/MCP-19 range.

---

## CI/CD Integration

```yaml
name: AI SAFE2 Security Scan
on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r scanner/requirements.txt
      - name: AI SAFE2 v3.1 scan
        run: |
          python -m scanner.cli scan . \
            --tier Tier2 \
            --report both \
            --output ai-safe2-report.json \
            --fail-under 70
```

---

## Data Integration

The current data model separates:

```text
skills/mcp/data/ai-safe2-controls-v3.0.json  stable 161-control core taxonomy
skills/mcp/data/mcp-profile-v3.1.json       CP.5.MCP v3.1 profile overlay
```

This is intentional. v3.1 changes the MCP profile without pretending the core framework grew from 161 to 180 controls.

---

## File Structure

```text
scanner/
├── README.md
├── cli.py
├── scanner.py
├── report.py
├── tests/
│   └── test_v31_mcp_profile.py
└── rules/
    ├── __init__.py
    ├── base.py
    ├── p1_sanitize.py
    ├── p2_audit.py
    ├── p3_failsafe.py
    ├── p4_monitor.py
    ├── p5_evolve.py
    ├── cross_pillar.py
    └── mcp_profile.py
```

---

## 🔗 Navigation

| Previous | Current | Next |
|---|---|---|
| [NEXUS](../NEXUS/) | **Scanner** | [Gateway](../gateway/) |

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [MCP Profile](../00-cross-pillar/cp5_mcp_server_security.md) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
