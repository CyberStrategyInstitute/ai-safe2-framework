<div align="center">

# Langflow Sovereign Runtime
### AI SAFE2 v3.0 Defense Package for Langflow (Visual DAG Builder + Webhook + MCP + RAG)

**Cyber Strategy Institute** · MIT License · Framework: AI SAFE² v3.0

</div>

---

> **Langflow is not a Python runtime framework you can wrap with a callback hook.**
>
> It's a visual DAG builder where nodes execute internally. You cannot intercept execution from outside the DAG. The sovereign runtime sits as an external API proxy — scanning every request before it reaches Langflow's HTTP endpoints — plus an inline DAG node that gates component outputs within the flow itself.
>
> Eight surfaces. Two enforcement layers. Zero dependencies.

---

## Why Langflow Requires a Different Architecture

Every other runtime in this series (LangChain, LangGraph, CrewAI, Make.com, Cursor) has a Python execution boundary you can intercept with a class wrapper or callback. Langflow's DAG executes internally. There is no hook.

The AI SAFE2 Langflow Sovereign Runtime implements two enforcement layers:

**Layer 1: External API Proxy** — scans all requests before they reach Langflow's HTTP endpoints. Deploy in your reverse proxy, API gateway, or application middleware.

**Layer 2: Inline DAG Node** — the `safe2_guardian_component.py` component drops directly into Langflow flows between data-fetching components and Agent nodes, intercepting the LF-COMP surface from within the DAG.

---

## Eight Surfaces. All Confirmed From Live Docs.

| Surface | Confirmed From | Risk | Method |
|---|---|---|---|
| **LF-WHK** | docs.langflow.org/webhook | Async background run — no output gate; unauthenticated = flow owner | `scan_webhook_payload()` |
| **LF-RUN** | docs.langflow.org/api | tweaks overrides ANY component field; default session = shared memory | `scan_run_request()` |
| **LF-GVAR** | docs.langflow.org/configuration-global-variables | X-LANGFLOW-GLOBAL-VAR-LANGFLOW_DATABASE_URL redirects prod DB | `scan_global_var_headers()` |
| **LF-KNOW** | docs.langflow.org/knowledge | RAG vector DB — poisoned doc persists for all future queries | `scan_knowledge_document()` |
| **LF-MCP** | docs.langflow.org/mcp-server | **AUTO-EXPOSE IS DEFAULT**: all projects exposed instantly on create | `scan_mcp_config()` |
| **LF-FLOW** | docs.langflow.org/concepts-flows-import | CustomComponent = raw Python via build engine; API key in JSON export | `scan_flow_json()` |
| **LF-INST** | docs.langflow.org/agents | system_prompt saved in flow JSON; affects ALL future sessions | `scan_agent_instructions()` |
| **LF-COMP** | DAG architecture | URL fetcher → injection → Agent node (multiple DAG hops) | `scan_component_output()` |

---

## The Most Critical Surface: LF-MCP (Default-On)

Confirmed verbatim from Langflow's documentation (June 2026):

> "When you create a Langflow project, Langflow automatically adds the project to your MCP server's configuration and makes the project's flows available as MCP tools."

The environment variable is `LANGFLOW_ADD_PROJECTS_TO_MCP_SERVERS`, which **defaults to True**.

Combined with `LANGFLOW_AUTO_LOGIN=true` (also a common default), you get an MCP server with no authentication exposing all your flows as tools to any connected MCP client. This is the highest-blast-radius default configuration in this series.

**Fix before enabling MCP:**
```bash
LANGFLOW_ADD_PROJECTS_TO_MCP_SERVERS=false
LANGFLOW_AUTO_LOGIN=false
```

---

## The Proxy + DAG Architecture

```
External Client
      │
      ▼
┌─────────────────────────────────┐
│   AI SAFE2 API Proxy Layer      │
│   scan_webhook_payload()        │  ← LF-WHK, LF-RUN, LF-GVAR
│   scan_run_request()            │
│   scan_global_var_headers()     │
└──────────────┬──────────────────┘
               │ clean requests only
               ▼
┌─────────────────────────────────┐
│   Langflow Server (:7860)       │
│   POST /api/v1/webhook/$FLOW    │
│   POST /api/v1/run/$FLOW        │
└──────────────┬──────────────────┘
               │ DAG execution
               ▼
┌─────────────────────────────────┐
│   [URL Fetcher] → [AI SAFE2     │
│   Guardian] → [Agent Node]      │  ← LF-COMP (safe2_guardian_component.py)
└─────────────────────────────────┘
```

---

## Package Contents

```
examples/langflow-sovereign-runtime/
│
├── enforcement/
│   ├── ai_safe2_engine.py          NEXUS kernel — stdlib only
│   ├── sovereign_langflow.py       8-surface Langflow enforcement class
│   └── __init__.py
│
├── langflow-component/
│   └── safe2_guardian_component.py Inline DAG node — drop into Langflow as CustomComponent
│
├── controls/
│   └── policy.yaml                 Machine-readable control registry
│
├── integrations/
│   ├── NEXUS-love-equation.md      Proxy pattern + unified score
│   ├── mcp-security.md             MCP safe configuration guide
│   └── langsmith-integration.md    AI SAFE2 + LangSmith observability
│
├── ci-cd/
│   └── github-actions-langflow-gate.yml
│
├── reports/                        Audit logs (gitignore)
├── smoke_test.py                   21/21 adversarial tests
├── requirements.txt
├── QUICKSTART.md
├── ANNOUNCEMENT.md
└── README.md
```

---

## Quick Start

```bash
cd examples/langflow-sovereign-runtime
PYTHONPATH=enforcement python3 smoke_test.py
# TOTAL: 21/21 -- SOVEREIGN BASELINE VERIFIED
```

---

## AI SAFE2 Pillar Coverage

| Pillar | Controls | Langflow Enforcement |
|---|---|---|
| P1 Sanitize-Isolate | P1.T1.2, P1.T1.5, P1.T1.9, P1.T1.10, P1.T1.4_ADV, P1.T2.5, S1.3, S1.5, S1.6 | All 8 LF surfaces |
| P2 Audit-Inventory | P2.T3.1, A2.5 | SHA-256 JSONL per session |
| P3 Fail-Safe | P3.T5.5 | Ops rate limiting |
| P4 Engage-Monitor | M4.5 | Global var header monitoring; MCP tool monitoring |
| P5 Evolve-Educate | E5.1 | Love Equation + GREEN/YELLOW/RED |
| CP Cross-Pillar | CP.4 | MCP project allowlist governance |

---

## Known Enforcement Gaps

1. **DAG internal execution** — Components between safe2_guardian nodes execute without enforcement. Place the guardian after every data-fetching component, not just at the first hop.
2. **Langflow UI direct actions** — Knowledge uploads, flow imports, and system_prompt edits via the Langflow browser UI bypass the proxy layer. Pair with Langflow's RBAC and SSO.
3. **Custom component validation depth** — The flow JSON scanner validates code fields in template nodes but doesn't execute the code. Complex obfuscated payloads may evade static pattern matching. Review all CustomComponent code manually before import.

---

## Connect to the NEXUS Mesh

```
examples/
├── langflow-sovereign-runtime/    ← THIS PACKAGE
├── make-sovereign-runtime/
├── xai-grok-sovereign-runtime/
├── lovable-sovereign-runtime/
├── manus-sovereign-runtime/
└── cursor-sovereign-runtime/
```

**MIT License — Cyber Strategy Institute**
*"Engineered Certainty for the Agentic Age."*
