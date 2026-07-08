<!-- stack: Cursor -->
<!-- description: Runtime controls for Cursor IDE chains, .cursor/rules injection surfaces, and AI-generated code execution. -->
<div align="center">

# Cursor Sovereign Runtime
### AI SAFE2 v3.0 Defense Package for Cursor (11+ CVEs, 8 Surfaces, 4 Architectural Attack Patterns)

**Cyber Strategy Institute** · MIT License · Framework: AI SAFE² v3.0

</div>

---

> **Cursor shipped 11+ CVEs in 2025-2026. The highest-CVSS is 9.9. One is currently unpatched.**
>
> CurXecute writes a malicious MCP server to your config and executes it immediately. MCPoison approves a benign server, then swaps the command. NomShub writes to your shell RC file for persistent access. CVE-2026-26268 escapes the sandbox on the next git operation.
>
> Each of these has a specific architectural pattern. Each has a specific gate. This package provides all eight.

---

## 8 Surfaces. 11+ CVEs. 4 Architectural Patterns.

| Surface | CVE / Name | CVSS | Method |
|---|---|---|---|
| **CU-RULES** | Pillar Security (invisible Unicode in .mdc) | — | `scan_rules_file()` |
| **CU-MCP** | CurXecute / CVE-2025-54135 | **8.6** | `scan_mcp_json()` |
| **CU-TRUST** | MCPoison / CVE-2025-54136 + TrustFall (unpatched) | 7.2 | `scan_mcp_server_registration()` |
| **CU-REPO** | CVE-2026-26268 + NomShub | **9.9** | `scan_repo_file()` |
| **CU-CMD** | CVE-2026-22708 (builtins bypass Auto-Run) | — | `scan_shell_command()` |
| **CU-IGNORE** | CVE-2025-64110 (.cursorignore bypass) | **8.7** | `scan_cursorignore()` |
| **CU-CLOUD** | Background agent cloud VM layer | — | `scan_cloud_agent_task()` |
| **CU-SUPPLY** | CVE-2025-64106 (MCP installer spoofing) | **8.8** | `scan_mcp_install()` |

---

## The Four Architectural Attack Patterns (Repello, May 2026)

**Pattern 1 — Pre-trust execution / TOFU bypass**
MCPoison and TrustFall. Approve once → command swapped silently. Project-local MCP servers execute without a separate user prompt.

**Pattern 2 — Indirect prompt injection → file write → RCE**
CurXecute. IPI in Slack/repo → agent writes `.cursor/mcp.json` → Cursor executes malicious MCP command under dev privileges.

**Pattern 3 — Sandbox escape via privileged side-channel**
CVE-2026-26268 (CVSS 9.9). Sandboxed agent writes `.git/config` → next git op executes hook out-of-sandbox. `.git/` was not enumerated in the sandbox boundary. NomShub follows the same pattern via shell RC files.

**Pattern 4 — Supply chain**
CVE-2025-64106 (installer spoofing), OpenVSX namespace squatting, unpinned `npx @latest`.

All four patterns are closed by gates in this package. A single MDM push (Cursor 2.5+) closes Patterns 2 and 3 at the platform level — but Patterns 1 and 4 are architectural and require enforcement regardless of version.

---

## Package Contents

```
examples/cursor-sovereign-runtime/
│
├── enforcement/
│   ├── ai_safe2_engine.py          NEXUS kernel — stdlib only
│   ├── sovereign_cursor.py         8-surface Cursor enforcement class
│   └── __init__.py
│
├── .cursor/
│   └── rules/
│       └── ai-safe2-sovereign.mdc  → Drop into .cursor/rules/ workspace
│
├── controls/
│   └── policy.yaml                 Machine-readable registry with CVE kill chains
│
├── integrations/
│   ├── nomshub-defense.md          CVE-2026-26268 + NomShub kill chain analysis
│   └── NEXUS-love-equation.md      MCPoison state + unified score
│
├── cursor-skill/
│   └── ai-safe2-cursor.md          Claude/Cursor skill for Cursor sessions
│
├── ci-cd/
│   └── github-actions-cursor-gate.yml
│
├── reports/                        Audit logs (gitignore)
├── smoke_test.py                   21/21 adversarial tests (maps to real CVEs)
├── requirements.txt
├── QUICKSTART.md
└── README.md
```

---

## Quick Start

```bash
cd examples/cursor-sovereign-runtime
PYTHONPATH=enforcement python3 smoke_test.py
# TOTAL: 21/21 -- SOVEREIGN BASELINE VERIFIED
```

**Highest-impact single action:** Pin Cursor to 2.5+ via MDM. Closes CVE-2026-26268 (CVSS 9.9), CurXecute, MCPoison, and .cursorignore bypass in one push.

---

## One-Line Integration

```python
from enforcement.sovereign_cursor import CursorSovereignRuntime

guard = CursorSovereignRuntime(
    allowed_mcp_servers=["github-mcp"],
    shell_command_allowlist=["git status", "npm test"],
)

guard.scan_rules_file(content, filename)         # CU-RULES
guard.scan_mcp_json(content, ".cursor/mcp.json") # CU-MCP (CurXecute)
guard.scan_mcp_server_registration(name, cmd)    # CU-TRUST (MCPoison)
guard.scan_repo_file(content, filepath)          # CU-REPO (CVE-2026-26268)
guard.scan_shell_command(cmd, context)           # CU-CMD (CVE-2026-22708)
guard.scan_cursorignore(content)                 # CU-IGNORE (CVE-2025-64110)
guard.scan_cloud_agent_task(task, repo_url)      # CU-CLOUD
guard.scan_mcp_install(package, install_cmd)     # CU-SUPPLY (CVE-2025-64106)
```

---

## AI SAFE2 Pillar Coverage

| Pillar | Controls | Cursor Enforcement |
|---|---|---|
| P1 Sanitize-Isolate | P1.T1.2, P1.T1.9, P1.T1.10, P1.T1.4_ADV, P1.T2.1, P1.T2.5, P1.T2.6, S1.3, S1.5, S1.6 | All 8 CU surfaces |
| P2 Audit-Inventory | P2.T3.1, A2.5 | SHA-256 JSONL + MCPoison state tracking |
| P3 Fail-Safe | F3.2 | Shell command governor |
| P4 Engage-Monitor | P4.T7.1, M4.5 | HITL gate on MCP; tool-misuse detection |
| P5 Evolve-Educate | E5.1 | Love Equation + GREEN/YELLOW/RED |
| CP Cross-Pillar | CP.9, CP.10 | Cloud agent sub-agent governance; HEAR for port/tool auth |

---

## Known Enforcement Gaps

1. **TrustFall (unpatched)** — Project-local MCP servers execute without approval prompt. Mitigate via managed workspace config: `"cursor.mcp.disableProjectLocalServers": true`
2. **94 unpatched Chromium CVEs** — Riding Cursor's Chromium release lag (OX Security). No mitigation in this package; enforce Cursor version updates via MDM.
3. **OpenVSX namespace squatting** — This package doesn't scan the full OpenVSX registry. Audit your installed extensions quarterly.
4. **Cloud agent VM enforcement** — `scan_cloud_agent_task()` validates the prompt, not the cloud VM's execution. Cloud VM-level enforcement requires Cursor's enterprise runtime controls.

---

## Connect to the NEXUS Mesh

```
examples/
├── cursor-sovereign-runtime/      ← THIS PACKAGE (series complete)
├── manus-sovereign-runtime/
├── lovable-sovereign-runtime/
├── xai-grok-sovereign-runtime/
└── make-sovereign-runtime/
```

**MIT License — Cyber Strategy Institute**
*"Engineered Certainty for the Agentic Age."*
