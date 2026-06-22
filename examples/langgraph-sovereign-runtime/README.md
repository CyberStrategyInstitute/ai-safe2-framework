<div align="center">

# LangGraph Sovereign Runtime
### AI SAFE² v3.0 Defense Package for LangGraph

[![AI SAFE² v3.0](https://img.shields.io/badge/AI_SAFE²-v3.0-cc6600?style=for-the-badge&labelColor=black)](https://github.com/CyberStrategyInstitute/ai-safe2-framework)
[![Tests](https://img.shields.io/badge/Tests-15%2F15_passing-brightgreen?style=flat-square)](./smoke_test.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../LICENSE)

**Cyber Strategy Institute** · [cyberstrategyinstitute.com](https://cyberstrategyinstitute.com)

</div>

---

## LangGraph vs LangChain: A Different Threat Model

LangGraph has no `BaseCallbackHandler`. Enforcement hooks into node functions directly.
Three surfaces are unique to LangGraph and absent from LangChain:

### 1. State Dict Injection at Node Boundaries (P1.T1.10)

The `state` dict flows node-to-node. A web-scraper node writes untrusted content
into `state["scraped_page"]`. That value re-enters the next node's input.
Without enforcement at node output, it's an unchecked IPI surface.

`StateGuard.scan_state_update()` scans **only the node's return dict** (the partial
state update — the diff). Not the full state. Never double-scans. ~80% cheaper
than full-state scanning on large graphs.

### 2. Supervisor Routing Key Hijack (S1.3)

`state["next"]` controls which node executes next. An injection payload that
rewrites this key redirects the entire graph to an unauthorized node.

`RoutingGuard.validate()` checks every routing key value against:
1. Injection pattern scan (P1.T1.2)
2. Declared node inventory (S1.3 — unauthorized targets blocked at ACT-3)

### 3. Subgraph Delegation Depth (CP.9)

LangGraph subgraphs are how you spawn child agents. Without a depth ceiling,
an orchestrator can recurse indefinitely.

`sovereign.enter_subgraph()` / `sovereign.exit_subgraph()` enforces:

| ACT Tier | Max Delegation Depth |
|---|---|
| ACT-2 | 5 hops |
| ACT-3 | 2 hops |
| ACT-4 | 3 hops |

---

## One-Line Integration

```python
from enforcement import SovereignStateGraph, ACTTier
from langgraph.graph import StateGraph, END

sovereign = SovereignStateGraph(
    act_tier=ACTTier.ACT3,
    declared_nodes=["researcher", "writer", "reviewer"],
    routing_key="next",
)

graph = StateGraph(MyState)
graph.add_node("researcher", sovereign.wrap_node("researcher", researcher_fn))
graph.add_node("writer",     sovereign.wrap_node("writer",     writer_fn))
graph.add_node("reviewer",   sovereign.wrap_node("reviewer",   reviewer_fn))
graph.set_finish_point("reviewer")
compiled = graph.compile()
result = compiled.invoke({"input": "Write a report on Q3."})
```

---

## Control Coverage

| Control | Name | Enforcement Point |
|---|---|---|
| **P1.T1.2** | Malicious Prompt Filtering | Node return value scan |
| **P1.T1.5** | Sensitive Data Masking | Node return credential scan |
| **P1.T1.10** | Indirect Injection Surface Coverage | `StateGuard.scan_state_update()` |
| **P1.T2.3** | API Gateway Restrictions | URL values in state updates |
| **S1.3** | Semantic Isolation Boundary | `RoutingGuard.validate()` |
| **S1.5** | Memory Governance Boundary | `protect_state_write()` |
| **F3.2** | Agent Recursion Limit Governor | Node execution ceiling |
| **F3.5** | Multi-Agent Cascade Containment | Node error isolation |
| **A2.5** | Semantic Execution Trace Logging | Per-node OCSF event + diff hash |
| **M4.5** | Tool-Misuse Detection Controls | Per-node call count ceiling |
| **P2.T3.6** | Compliance Validation | `compliance_report()` |
| **CP.3** | ACT Capability Tiers 1-4 | Constructor `act_tier` |
| **CP.4** | Agentic Control Plane Governance | `register_nhi()` |
| **CP.9** | Subgraph Replication Governance | `enter_subgraph()` / `exit_subgraph()` |
| **CP.10** | HEAR Doctrine | HEAR gate on node output values |

---

## Subgraph Pattern (CP.9)

```python
# Orchestrator invoking a child agent as a subgraph
sovereign = SovereignStateGraph(act_tier=ACTTier.ACT3)  # max depth: 2

sovereign.enter_subgraph("research-subgraph")
try:
    result = research_graph.invoke(state)
finally:
    sovereign.exit_subgraph()

# Attempting a 3rd hop raises CircuitTripped[CP.9]
```

---

## NEXUS Mesh

```python
from enforcement.ai_safe2_engine import AISAFE2Engine, ACTTier

shared_engine = AISAFE2Engine(act_tier=ACTTier.ACT3)

# Pass to LangChain handler AND LangGraph sovereign
from enforcement import SovereignStateGraph
sovereign_lg = SovereignStateGraph(engine=shared_engine)
# → One compliance score, one SHA-256 audit chain, one HEAR gate
```

---

*AI SAFE² v3.0 | Cyber Strategy Institute | cyberstrategyinstitute.com*
