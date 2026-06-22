# NEXUS Mesh — Shared Engine Across Runtimes
## AI SAFE² v3.0 Multi-Framework Sovereign Architecture

---

## What Is the NEXUS Mesh?

Each sovereign runtime package ships an `AISAFE2Engine` kernel — one Python class,
zero external dependencies, stdlib only. The critical design choice: **one engine
instance can be shared across all six packages**.

When you do that, you get:

| Capability | Single-Engine | Per-Package Engines |
|---|---|---|
| Compliance score | Unified across all frameworks | Siloed per-framework |
| Audit chain | One SHA-256 chain, all events | Fragmented chains |
| F3.2 recursion ceiling | Counts across LangChain + LangGraph + CrewAI | Each framework resets its own counter |
| CP.10 HEAR gate | One gate, any framework | Must trigger separately per-framework |
| NHI registry | All agents in one inventory | Fragmented registries |

**TL;DR:** Share one engine if you want NEXUS-level governance. Separate engines if
you want framework-level governance with independent compliance scores.

---

## Setup: Single Shared Engine

```python
from enforcement.ai_safe2_engine import AISAFE2Engine, ACTTier
from pathlib import Path

# Create once at application startup
nexus_engine = AISAFE2Engine(
    runtime_id="prod-nexus-mesh",
    act_tier=ACTTier.ACT3,
    max_tool_calls=200,           # F3.2: ceiling across ALL frameworks combined
    max_identical_calls=4,        # M4.5: per-tool loop detection
    allowed_domains=[
        "api.openai.com",
        "api.anthropic.com",
        "your-api.company.com",
    ],
    audit_log_dir=Path("/var/log/ai_safe2"),
)

# Register the mesh itself as a CP.4 control plane entity
nexus_engine.register_nhi(
    agent_id="nexus-mesh-prod-001",
    owner_of_record="ai-ops@yourcompany.com",
    act_tier=ACTTier.ACT3,
    tool_authorizations=["*"],    # mesh-level registration
    control_plane_id="nexus-cp-001",
)
```

---

## Connecting LangChain

```python
from enforcement.sovereign_langchain import SovereignCallbackHandler, SovereignLangChain

langchain_handler = SovereignCallbackHandler(engine=nexus_engine)
sovereign_lc = SovereignLangChain(engine=nexus_engine)

# Standard usage
result = langchain_chain.invoke(
    inputs,
    config={"callbacks": [langchain_handler]}
)
```

---

## Connecting LangGraph

```python
from examples.langgraph_sovereign_runtime.enforcement.sovereign_langgraph import SovereignStateGraph

# Pass the shared engine — state diff scanning uses the same violation registry
sovereign_lg = SovereignStateGraph(engine=nexus_engine)
graph = sovereign_lg.wrap_graph(your_state_graph)
```

---

## Connecting CrewAI

```python
from examples.crewai_sovereign_runtime.enforcement.sovereign_crewai import SovereignCrew

# Agent identity poisoning scan shares the same injection patterns
sovereign_crew = SovereignCrew(engine=nexus_engine)
crew = sovereign_crew.wrap_crew(your_crew)
```

---

## Connecting AutoGen 0.4

```python
from examples.autogen_sovereign_runtime.enforcement.sovereign_autogen import SovereignRuntime

# AutoGen's CodeExecutorAgent exec() surface adds CP.8 mandatory
# The shared engine's CP.8 events feed into the same audit chain
sovereign_ag = SovereignRuntime(engine=nexus_engine)
```

---

## One Compliance Report for the Whole Stack

```python
# After any mix of LangChain / LangGraph / CrewAI / AutoGen invocations:
report = nexus_engine.compliance_report()
print(report)

# Real-time status
status = nexus_engine.get_status()
# {
#   "compliance_score": 94.0,
#   "alignment_band": "GREEN",
#   "total_violations": 3,
#   "total_tool_calls": 47,   ← counted across ALL frameworks
#   "nhi_count": 4,
#   "controls_active": ["P1.T1.2", ..., "CP.10"],
#   ...
# }
```

---

## One Audit Chain for All Events

All six frameworks emit to the same OCSF 1.1 log file when sharing an engine:

```jsonl
{"class_uid":6001,"finding_info":{"title":"NHI_REGISTERED","source":"agent:langchain-prod-01"},"metadata":{"control_id":"CP.4"},...}
{"class_uid":6001,"finding_info":{"title":"CONTENT_VIOLATION","source":"tool_output:web_scraper"},"metadata":{"control_id":"P1.T1.10"},...}
{"class_uid":6001,"finding_info":{"title":"CHAIN_ERROR_ISOLATED","source":"chain:langgraph-supervisor"},"metadata":{"control_id":"F3.5"},...}
{"class_uid":6001,"finding_info":{"title":"HEAR_GATE_TRIGGERED","source":"action_gate"},"metadata":{"control_id":"CP.10"},...}
```

The SHA-256 chain spans all frameworks. Any tampering with any event — regardless
of which framework emitted it — breaks the chain.

---

## When NOT to Share an Engine

| Scenario | Recommended |
|---|---|
| Independent services across different teams | Separate engines per service |
| Different ACT tiers per framework | Separate engines (different tiers) |
| Regulatory isolation (separate audit scopes) | Separate engines per scope |
| Multi-tenant (per-customer isolation) | One engine per tenant |
| Development vs production | Always separate engines |

---

## Thread Safety

`AISAFE2Engine` uses list appends and dict operations that are GIL-protected in
CPython. For production with `asyncio` or multi-threaded LangChain, wrap the engine
in a lock for the F3.2 counter and M4.5 identical-call dict:

```python
import threading
engine._lock = threading.Lock()

# Then in your hot path:
with engine._lock:
    engine.record_tool_call(tool_name, args)
```

Full async-safe version is on the roadmap for v3.1.

---

*AI SAFE² v3.0 | Cyber Strategy Institute | NEXUS Mesh Architecture*
