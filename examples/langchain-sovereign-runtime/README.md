<div align="center">

# LangChain Sovereign Runtime
### AI SAFE² v3.0 Defense Package for LangChain

[![AI SAFE² v3.0](https://img.shields.io/badge/AI_SAFE²-v3.0-cc6600?style=for-the-badge&labelColor=black)](https://github.com/CyberStrategyInstitute/ai-safe2-framework)
[![Tests](https://img.shields.io/badge/Tests-15%2F15_passing-brightgreen?style=flat-square)](./smoke_test.py)
[![ACT Tiers](https://img.shields.io/badge/CP.3-ACT_1--4_enforced-orange?style=flat-square)](https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/00-cross-pillar)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../LICENSE)

**Cyber Strategy Institute** · [cyberstrategyinstitute.com](https://cyberstrategyinstitute.com)

</div>

---

## Why This Exists

LangChain is the most widely deployed Python framework for LLM applications. By default, it has no enforcement boundary: tool outputs flow directly into the agent's context window, the `AgentExecutor` loop has no hard ceiling, and `ConversationBufferMemory` accepts any write.

That means:

| Gap | Consequence |
|---|---|
| Tool outputs are untrusted but unsanitized | Indirect Prompt Injection via web scrapes, retrieved docs, API returns |
| `AgentExecutor` loops with no hard limit | Runaway agents, unbounded token spend, Denial-of-Wallet |
| Memory writes are ungoverned | Long-horizon memory poisoning — corrupts future sessions |
| No credential scan on final output | API keys, private keys, PII leak from chain output to logs |

**This package enforces AI SAFE² v3.0 controls at the enforcement points that matter, without requiring any changes to your chains.**

---

## What Makes LangChain's Threat Surface Unique

Every AI SAFE² integration hooks into the framework at its specific critical surfaces.
LangChain's are:

```
User input / document retrieval
        │
        ▼
┌───────────────────────────────────────────┐
│  P1.T1.2: on_llm_start / on_chat_model_start  │  ← Scan before LLM sees it
│  Malicious Prompt Filtering               │
└─────────────────┬─────────────────────────┘
                  │
        ▼ LLM generates
┌───────────────────────────────────────────┐
│  M4.5 + F3.2: on_tool_start               │  ← Record call; enforce ceiling
│  Tool-Misuse Detection + Recursion Limit  │
└─────────────────┬─────────────────────────┘
                  │
        ▼ Tool executes and returns
┌───────────────────────────────────────────┐
│  P1.T1.10: on_tool_end                    │  ← THE critical IPI surface
│  Indirect Injection Surface Coverage      │     Tool output scanned before
│  S1.3: Semantic Isolation Boundary        │     it re-enters model context
└─────────────────┬─────────────────────────┘
                  │
        ▼ Chain completes
┌───────────────────────────────────────────┐
│  P1.T1.5: on_chain_end / on_llm_end       │  ← Credential scan on output
│  Sensitive Data Masking                   │
└───────────────────────────────────────────┘
        │
        ▼ Memory write
┌───────────────────────────────────────────┐
│  S1.5: protect_memory()                   │  ← Authorize before every write
│  Memory Governance Boundary Controls      │
└───────────────────────────────────────────┘
```

---

## One-Line Integration

**Callback (no chain changes required):**
```python
from enforcement import SovereignCallbackHandler, ACTTier

chain.invoke(
    {"input": user_input},
    config={"callbacks": [SovereignCallbackHandler(act_tier=ACTTier.ACT3)]}
)
```

**Full wrapper (adds tool protection + memory governance):**
```python
from enforcement import SovereignLangChain, ACTTier

sovereign = SovereignLangChain(
    act_tier=ACTTier.ACT3,
    allowed_domains=["api.example.com", "docs.mycompany.com"],
)
protected_tool = sovereign.wrap_tool(my_search_tool)
sovereign.protect_memory(memory)
result = sovereign.run(chain, {"input": user_input})
```

---

## AI SAFE² Control Coverage

All control IDs verified from [github.com/CyberStrategyInstitute/ai-safe2-framework](https://github.com/CyberStrategyInstitute/ai-safe2-framework).

| Control | Name | Enforcement Point | ACT Tier |
|---|---|---|---|
| **P1.T1.2** | Malicious Prompt Filtering | `on_llm_start`, `on_chat_model_start` | All |
| **P1.T1.5** | Sensitive Data Masking | `on_chain_end`, `on_llm_end` | All |
| **P1.T1.10** | Indirect Injection Surface Coverage | `on_tool_end` (primary IPI surface) | All |
| **P1.T2.3** | API Gateway Restrictions | `wrap_tool()` domain allowlist | ACT-2+ |
| **S1.3** | Semantic Isolation Boundary | `isolate_context()` on tool outputs | ACT-3+ |
| **S1.5** | Memory Governance Boundary | `protect_memory()` write gate | ACT-3+ |
| **F3.2** | Agent Recursion Limit Governor | `on_tool_start` ceiling enforcement | ACT-2+ |
| **F3.5** | Multi-Agent Cascade Containment | `on_chain_error` isolation | ACT-2+ |
| **A2.5** | Semantic Execution Trace Logging | All callback events (OCSF 1.1) | All |
| **M4.5** | Tool-Misuse Detection Controls | Per-tool frequency baseline | ACT-2+ |
| **P2.T3.6** | Compliance Validation | `compliance_report()` | All |
| **CP.3** | ACT Capability Tiers 1-4 | Constructor `act_tier` parameter | All |
| **CP.4** | Agentic Control Plane Governance | `register_nhi()` — NHI identity | All |
| **CP.8** | Catastrophic Risk Threshold | `emit_cp8_event()` — FATAL events | ACT-3+ |
| **CP.10** | HEAR Doctrine | `check_hear_gate()` — Class-H actions | ACT-3+ |

---

## Quick Start

```bash
git clone https://github.com/CyberStrategyInstitute/ai-safe2-framework
cd examples/langchain-sovereign-runtime

# Install
pip install -r requirements.txt

# Verify baseline
python smoke_test.py
# Expected: 15/15 — SOVEREIGN BASELINE VERIFIED

# Static pre-flight
bash validation/pass1_static.sh

# Runtime validation
bash validation/pass2_runtime.sh
```

See [QUICKSTART.md](./QUICKSTART.md) for the full 15-minute setup.

---

## ACT Tier Behavior

CP.3 governs fail-open vs fail-closed. Pass `act_tier` to the handler or engine:

| Tier | Name | On Violation | When to Use |
|---|---|---|---|
| `ACT1` | Assisted | Log only — never raises | Human reviews all outputs |
| `ACT2` | Supervised | Log + SSRF/path blocks raise | Agent acts with checkpoints |
| `ACT3` | Autonomous | All critical violations raise | Autonomous production agents |
| `ACT4` | Orchestrator | ACT-3 + HEAR gate mandatory | Agents that control other agents |

---

## NEXUS Mesh: Share One Engine Across All Runtimes

```python
from enforcement.ai_safe2_engine import AISAFE2Engine, ACTTier
from enforcement.sovereign_langchain import SovereignCallbackHandler

# LangGraph, CrewAI, AutoGen, n8n packages accept the same engine
shared_engine = AISAFE2Engine(runtime_id="prod-nexus", act_tier=ACTTier.ACT3)

langchain_handler = SovereignCallbackHandler(engine=shared_engine)
# → Pass shared_engine to SovereignStateGraph, SovereignCrew, etc.
# → One compliance score. One audit chain. One HEAR gate.
```

See [integrations/NEXUS-mesh.md](./integrations/NEXUS-mesh.md).

---

## What Users See When the Engine Blocks Something

```
🚨 [AI SAFE² CRITICAL] [P1.T1.2] direct_override detected in 'llm_input_chat'
🚨 [AI SAFE² HIGH]     [P1.T1.5] anthropic_api_key detected in 'chain_output:text'
🚨 [AI SAFE² CRITICAL] [P1.T1.10] jailbreak_persona detected in 'tool_output:web_scraper'
🚨 [AI SAFE² CRITICAL] [F3.2] Tool call ceiling 50 reached
🚨 [AI SAFE² CRITICAL] [M4.5] Loop: 'calculator' identical args 4x
🛑 [AI SAFE² FATAL]    [CP.8] Catastrophic risk threshold triggered
```

Every alert includes the exact AI SAFE² control ID, source context, and is written
to a tamper-evident SHA-256 chain OCSF 1.1 audit log.

---

## Package Structure

```
langchain-sovereign-runtime/
├── README.md                    ← You are here
├── QUICKSTART.md                ← 15-minute setup
├── SECURITY.md                  ← Vulnerability disclosure
├── ANNOUNCEMENT.md              ← GitHub release announcement
├── requirements.txt
├── .env.example
├── core/
│   ├── IDENTITY.md              ← CP.4: NHI registration template
│   ├── SOUL.md                  ← S1.3: behavioral containment
│   ├── TOOLS.md                 ← P1.T2.5: tool authorization
│   └── MEMORY.md                ← S1.5: memory governance policy
├── enforcement/
│   ├── ai_safe2_engine.py       ← NEXUS kernel (all controls, no external deps)
│   ├── sovereign_langchain.py   ← LangChain-specific enforcement
│   └── __init__.py
├── controls/
│   └── policy.yaml              ← Machine-readable control registry
├── smoke_test.py                ← 15/15 adversarial tests
├── validation/
│   ├── pass1_static.sh          ← Import, config, policy integrity
│   └── pass2_runtime.sh         ← Live enforcement verification
├── integrations/
│   ├── NEXUS-mesh.md            ← Multi-framework shared engine guide
│   └── langsmith-integration.md ← LangSmith + AI SAFE² tracing
└── ci-cd/
    └── github-actions-langchain-safe.yml
```

---

## Related Examples

| Example | How to Connect |
|---|---|
| [langgraph-sovereign-runtime](../langgraph-sovereign-runtime/) | Pass shared `AISAFE2Engine` instance |
| [crewai-sovereign-runtime](../crewai-sovereign-runtime/) | Pass shared `AISAFE2Engine` instance |
| [autogen-sovereign-runtime](../autogen-sovereign-runtime/) | Pass shared `AISAFE2Engine` instance |
| [mcp-security-toolkit](../mcp-security-toolkit/) | CP.5.MCP pre-scores any MCP server before use in tools |
| [hermes-sovereign-runtime](../hermes-sovereign-runtime/) | Full Docker stack pattern |

---

*AI SAFE² v3.0 | Cyber Strategy Institute | [cyberstrategyinstitute.com](https://cyberstrategyinstitute.com)*
