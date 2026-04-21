# AI SAFE² v3.0 Scanner

Static analysis engine for AI agents, agentic workflows, and AI-integrated codebases.
Scans against 161 AI SAFE² v3.0 controls across 5 pillars and the CP.1-CP.10 Cross-Pillar Governance layer.

## Part of the AI SAFE² v3.0 Ecosystem

| Surface | Tool | When |
| :--- | :--- | :--- |
| **Design-time** | SKILL.md + MCP Server (`skills/`) | While designing and building |
| **Pre-commit / CI** | Scanner (`scanner/`) — **you are here** | Before code reaches production |
| **Runtime** | Gateway (`gateway/`) | In production |

For n8n Logic Guard, GitHub Actions integration, and Docker Compose patterns, see:
→ [INTEGRATIONS.md](../INTEGRATIONS.md)

---

## What v3.0 Detects

| Category | Controls | Examples |
| :--- | :--- | :--- |
| Secrets & NHI | P1.T1.4_ADV | OpenAI/Anthropic/AWS keys, GitHub tokens, private keys, high-entropy strings |
| Injection surfaces | P1.T1.2, P1.T1.10, S1.6 | Prompt injection, indirect injection (emails, RAG, tool outputs), cognitive injection |
| Memory governance | S1.5, A2.6 | Vector DB writes without governance wrappers, RAG updates without hash tracking |
| No-code platforms | S1.7 | n8n expression injection, n8n credential exposure (CVE-2026-25049 class) |
| Unsafe execution | P1.T2.1 | `shell=True`, `eval()`, `exec()`, `os.system()` |
| Network exposure | P1.T2.2 | Binding to `0.0.0.0` |
| Recursion / loops | F3.2, P3.T5.1 | Tool-calling chains and loops without depth limits |
| Cascade risk | F3.5, P3.T5.8 | Multi-agent pipelines without blast radius containment |
| Missing HITL | P4.T7.1 | Email send, delete, payment calls without human approval gates |
| Cloud platforms | M4.8 | Bedrock UpdateGuardrail API without monitoring (confirmed attack path) |
| Tool misuse | M4.5 | Tool definitions without invocation baseline monitoring |
| Model supply chain | A2.3, P1.T1.9 | Model loading without hash verification or provenance ledger |
| Missing logging | A2.5, P4.T8.3 | LLM calls without execution trace logging or SIEM integration |
| Vulnerable deps | P5.T9.4 | Known-CVE versions of LangChain, OpenAI, Transformers, PyTorch |
| Agent spawning | CP.9 | Sub-agent creation without lineage tokens or delegation hop limits |
| Missing HEAR | CP.10 | ACT-3/4 configs without `hear_agent_of_record` field |
| Missing CRT | CP.8 | Autonomous agents without Catastrophic Risk Threshold definitions |
| AST structural | CP.9, M4.5, P3.T5.4 | Python AST analysis for agent topology and structural gaps |

---

## Quick Start

```bash
# Install
pip install -r scanner/requirements.txt

# Scan current directory
python -m scanner.cli scan .

# Scan with tier threshold
python -m scanner.cli scan ./my-agent --tier Tier2

# Generate compliance report (JSON + SARIF)
python -m scanner.cli scan . --report both --output report.json

# Fail CI/CD if score below 80
python -m scanner.cli scan . --fail-under 80

# Quiet mode (report only, no console output)
python -m scanner.cli scan . --quiet --report json
```

---

## What the Output Tells You

**Score (0-100):** Starts at 100, deducted by severity (CRITICAL -10, HIGH -5, MEDIUM -2, LOW -1).

**Verdict:** PASS (≥90) | AT RISK (≥70) | FAIL (≥50) | CRITICAL FAIL (<50)

**ACT Tier Estimate:** Inferred from code signals — unattended execution, agent spawning, persistent memory, tool access. HEAR and CP.9 flags appear automatically when the tier warrants them.

**Risk Score:** `CVSS_estimate + ((100 - Pillar_Score) / 10) + (AAF_estimate / 10)`. Static-analysis estimates only — use the MCP server `risk_score` tool for precise AAF calculation.

**Governance Gaps:** Structural gaps detected from code patterns — missing HEAR designation, missing CRT documentation, missing A2.5 trace logging.

**32-Framework Compliance Map:** Every finding maps to the applicable frameworks. The JSON report shows pass/fail status for all 32 frameworks (NIST AI RMF, ISO 42001, EU AI Act, SOC 2, HIPAA, GDPR, DORA, FedRAMP, CMMC 2.0, PCI-DSS v4, and 22 more).

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/ai-safe2-scan.yml
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
      - name: AI SAFE2 v3.0 Scan
        run: |
          python -m scanner.cli scan . \
            --tier Tier2 \
            --report both \
            --output ai-safe2-report.json \
            --fail-under 70
      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: ai-safe2-report
          path: ai-safe2-report.json
      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: ai-safe2-report.sarif.json
```

---

## Controls JSON Integration

The scanner automatically locates `ai-safe2-controls-v3.0.json` from `skills/mcp/data/`.
When found, findings are enriched with:
- Full control name and description
- Compliance framework mappings (all 32 frameworks)
- ACT tier applicability
- Builder problem framing

If the JSON is not found, the scanner degrades gracefully — it still runs all rules, just with less metadata in the output.

To specify a custom path:
```bash
python -m scanner.cli scan . --controls-json /path/to/ai-safe2-controls-v3.0.json
```

---

## v2.1 to v3.0 Upgrade Summary

| | v2.1 | v3.0 |
| :--- | :--- | :--- |
| Patterns | 7 regex | 40+ rules across all 5 pillars + CP |
| Controls | 4 | 30+ |
| Analysis | Regex + entropy | Regex + entropy + Python AST |
| Config files | None | n8n JSON, YAML agent configs, requirements.txt |
| ACT tier | None | Estimated from code signals |
| HEAR check | None | CP.10 flags on ACT-3/4 indicators |
| CP.9 check | None | Lineage and delegation hop detection |
| Risk formula | `100 - penalty` | v3.0: CVSS + Pillar + AAF |
| Compliance report | 2 ISO clauses | All 32 frameworks |
| Output formats | JSON only | JSON + SARIF |

---

## File Structure

```
scanner/
├── README.md
├── requirements.txt
├── __init__.py
├── cli.py           — Command-line interface
├── scanner.py       — Main scan engine + ACT tier estimation
├── report.py        — 32-framework compliance report + SARIF
└── rules/
    ├── __init__.py
    ├── base.py          — Rule dataclass, Finding, utilities
    ├── p1_sanitize.py   — P1 controls + S1.3-S1.7
    ├── p2_audit.py      — P2 controls + A2.3-A2.6
    ├── p3_failsafe.py   — P3 controls + F3.2-F3.5
    ├── p4_monitor.py    — P4 controls + M4.4-M4.8
    ├── p5_evolve.py     — P5 controls + E5.1, E5.4
    └── cross_pillar.py  — CP.3 ACT tier, CP.8, CP.9, CP.10
```

---

*AI SAFE² v3.0 | Cyber Strategy Institute | [cyberstrategyinstitute.com/ai-safe2/](https://cyberstrategyinstitute.com/ai-safe2/)*
