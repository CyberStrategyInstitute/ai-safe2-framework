<!-- AI-SAFE2-UX:START -->
[![AI SAFE² v3.1](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../../README.md)
[![Surface: Example](https://img.shields.io/badge/Surface-Example-820F1A?style=flat-square)](../README.md)
[![Context: v3.1 Current](https://img.shields.io/badge/Context-v3.1_Current-808080?style=flat-square)](../../docs/REPOSITORY-UX-STANDARD.md)

[Framework Home](../../README.md) | [Examples Index](../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [AISM](../../AISM/) | [NEXUS](../../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

> **Current framework context:** AI SAFE² v3.1. This example may preserve historical component versions or earlier framework references where they describe when the implementation was created. For current conformance, use the v3.1 framework and applicable profile requirements.
<!-- AI-SAFE2-UX:END -->

<div align="center">

# Lovable Sovereign Runtime
### AI SAFE2 v3.0 Defense Package for Lovable Agent mode + MCP

**Cyber Strategy Institute** · MIT License · Framework: AI SAFE² v3.0

</div>

---

> **Lovable doesn't just suggest code. It writes, deploys, and executes against your live production database on your behalf.**
>
> That is not a figure of speech. `query_database` runs with your full database permissions. `deploy_project` ships to production. Agent mode writes and commits code directly. The workspace knowledge you save is injected into every future session, workspace-wide, until you manually remove it.
>
> Six attack surfaces. None of them are bugs. All of them are unsecured by default.
>
> This package is the enforcement boundary.

---

## Why Lovable Has a Fundamentally Different Architecture

Every other runtime in this series wraps a Python runtime or a CLI tool.
Lovable is a no-code AI builder that autonomously writes, deploys, and
executes — against your live database — in a production environment.

The attack surface is not the agent's code. It's what the agent does.

| Surface | Confirmed From Live Docs | AI SAFE2 Control | Method |
|---|---|---|---|
| **LV-KNOW** | Knowledge "always included in context" across ALL projects, permanently | `P1.T1.10`, `S1.3`, `S1.5` | `scan_workspace_knowledge()` |
| **LV-PLAN** | Plan approval immediately triggers Agent mode execution — no second confirm | `P1.T1.10`, `P4.T7.1` | `scan_plan()` |
| **LV-SQL** | `query_database` "runs with your full database permissions. Read, write, and schema changes." | `P1.T2.5`, `S1.3` | `scan_sql_query()` |
| **LV-MCP** | "Scope is your full account, not one project. Tool calls use real credits and edit real projects." | `P1.T2.5`, `CP.4`, `M4.5` | `scan_mcp_scope()` |
| **LV-BUILD** | Agent writes and deploys production code — eval(), env leaks, hardcoded keys go live | `P1.T1.4_ADV`, `S1.5` | `scan_generated_code()` |
| **LV-SUBAGENT** | Subagents read ALL project files including .env and private keys, report findings to main agent | `P1.T2.6`, `S1.5` | `scan_subagent_file_access()` |

All surface descriptions are verified against live Lovable documentation (June 2026).

---

## Threat Analysis

### LV-KNOW — Workspace-Wide Persistent Injection

Workspace knowledge is injected into every future Lovable agent context across every project — permanently, until manually removed. It supports 10,000 characters. That's 10,000 characters of persistent attack surface shared across your entire workspace.

**Attack chain:** An attacker with workspace admin credentials (phished, credential-stuffed, or social-engineered) saves malicious instructions to workspace knowledge. From that point forward, every Lovable build in every project follows those instructions — exfiltrating code, building backdoors, disabling auth — silently, across all future sessions.

`scan_workspace_knowledge()` validates content before it reaches the knowledge field, blocking injection patterns, embedded credentials, and hidden Unicode (S1.6) invisible in the Lovable UI but readable by the LLM.

### LV-SQL — Database Owner Execution

`query_database` (Lovable MCP) is documented as running "with your full database permissions. Read, write, and schema changes." This is not a misconfiguration — it's the intended behavior. It means:

- No RLS filtering. The query runs as the database owner, bypassing row-level security entirely.
- `DROP TABLE users;` executes immediately. No confirmation prompt.
- `ALTER TABLE users DISABLE ROW LEVEL SECURITY;` makes your auth model meaningless.
- `CREATE FUNCTION ... SECURITY DEFINER` escalates privilege silently.

`scan_sql_query()` blocks all destructive patterns, RLS bypass, privilege escalation, and SQL injection signatures before the query reaches `query_database`.

### LV-MCP — Full-Account OAuth Token

The Lovable MCP server tokens are full-account scoped. "Whatever client you connect can list, read, and edit every project you have access to in Lovable." There is no per-project token scoping available. A compromised MCP client = access to all your Lovable projects, all your databases, all your deployments.

`scan_mcp_scope()` enforces a project allowlist (CP.4) and blocks high-privilege scopes and destructive tools before any MCP call.

### LV-SUBAGENT — Subagent File Exfiltration (New Surface)

This surface was not in the prior design. It was confirmed from live Lovable subagent documentation: subagents "can search your project, inspect files" and "report their findings back to the main Lovable agent." Subagents start with fresh context — they don't know what they're looking for — but they can read any file in your project, including `.env`, private keys, and service account credentials.

`scan_subagent_file_access()` intercepts file path lists before subagents read them, blocking access to credential files whose contents would appear in subagent findings and potentially in agent responses.

---

## Package Contents

```
examples/lovable-sovereign-runtime/
│
├── enforcement/
│   ├── ai_safe2_engine.py          NEXUS kernel — stdlib only, all 5 pillars + CP
│   ├── sovereign_lovable.py        6-surface Lovable enforcement class
│   └── __init__.py
│
├── workspace-knowledge/
│   └── ai-safe2-workspace-knowledge.md  → Paste into Lovable Settings → Knowledge
│
├── lovable-skill/
│   └── ai-safe2-lovable.md         → Claude/Cursor skill for Lovable sessions
│
├── controls/
│   └── policy.yaml                 Machine-readable control registry
│
├── integrations/
│   ├── NEXUS-love-equation.md      Cross-framework mesh + SIEM
│   └── mcp-server-security.md      MCP project allowlist + tool risk matrix
│
├── ci-cd/
│   └── github-actions-lovable-gate.yml
│
├── reports/                        Audit logs (gitignore this directory)
├── smoke_test.py                   21/21 adversarial test suite
├── requirements.txt
├── QUICKSTART.md
└── README.md
```

---

## Quick Start

```bash
cd examples/lovable-sovereign-runtime
PYTHONPATH=enforcement python3 smoke_test.py
# Expected: 21/21 -- SOVEREIGN BASELINE VERIFIED
```

**Highest-impact first action:** Drop `workspace-knowledge/ai-safe2-workspace-knowledge.md` into Lovable → Settings → Knowledge → Workspace knowledge. This applies trust boundary rules to every future agent session in your workspace immediately — no code required.

---

## One-Line Integration

```python
from enforcement.sovereign_lovable import LovableSovereignRuntime

guard = LovableSovereignRuntime(
    allowed_mcp_projects=["proj-dev-001", "proj-staging-002"],
)

# LV-KNOW: before saving knowledge
guard.scan_workspace_knowledge(knowledge_content, scope="workspace")

# LV-PLAN: before approving a plan
guard.scan_plan(plan_text, project_id="proj-dev-001")

# LV-SQL: before every query_database call
guard.scan_sql_query(sql, project_id="proj-dev-001")

# LV-MCP: before MCP client actions
guard.scan_mcp_scope(["projects:read"], ["proj-dev-001"], tool_name="get_project")

# LV-BUILD: after generation, before deploy
guard.scan_generated_code(code_content, filename="src/api/route.ts")

# LV-SUBAGENT: before subagent reads files
guard.scan_subagent_file_access(file_paths, project_id="proj-dev-001")
```

---

## AI SAFE2 Pillar Coverage

| Pillar | Controls | Lovable Enforcement |
|---|---|---|
| P1 Sanitize-Isolate | P1.T1.2, P1.T1.10, P1.T1.4_ADV, P1.T1.1, P1.T2.5, P1.T2.6, S1.3, S1.5, S1.6 | All 6 LV surfaces |
| P2 Audit-Inventory | P2.T3.1, A2.5 | SHA-256 JSONL audit chain per session |
| P3 Fail-Safe | P3.T5.5 | Credit ceiling + session rate limiter |
| P4 Engage-Monitor | P4.T7.1, M4.5 | HITL gate on plan approval; MCP tool monitoring |
| P5 Evolve-Educate | E5.1 | Love Equation score + GREEN/YELLOW/RED band |
| CP Cross-Pillar | CP.4, CP.10 | Project allowlist governance; HEAR for HITL authority |

---

## Known Enforcement Gaps

1. **Lovable UI direct actions** — Knowledge edits and plan approvals made directly in the Lovable browser UI bypass this package. Enforce at the organizational level via workspace SSO and admin controls.
2. **MCP OAuth token scope** — Lovable does not expose per-project token scoping. The project allowlist in this package is enforced client-side — it is not enforced by Lovable's server.
3. **Subagent file path interception** — `scan_subagent_file_access()` requires that your orchestration layer intercepts subagent file path lists. If you call Lovable via the MCP server without an interceptor, this gate does not apply.

---

## Connect to the NEXUS Mesh

```
examples/
├── lovable-sovereign-runtime/     ← THIS PACKAGE
├── make-sovereign-runtime/
├── xai-grok-sovereign-runtime/
├── manus-sovereign-runtime/       ← Next
└── cursor-sovereign-runtime/
```

**MIT License — Cyber Strategy Institute**
*"The only AI governance framework built by reverse-engineering production failures, not compliance checklists."*

<!-- AI-SAFE2-UX-FOOTER:START -->
---

### Repository navigation

[Examples Index](../README.md) | [Framework Home](../../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [NEXUS](../../NEXUS/) | [Scanner](../../scanner/README.md) | [MCP Profile](../../00-cross-pillar/cp5_mcp_server_security.md)

*AI SAFE² v3.1 | Cyber Strategy Institute*
<!-- AI-SAFE2-UX-FOOTER:END -->
