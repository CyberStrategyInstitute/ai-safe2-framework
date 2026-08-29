<div align="center">

# NEXUS-A2A v0.3

**Non-repudiable, Extensible, eXecutive-Unified, Sovereign Agent-to-Agent Governance**

[![NEXUS](https://img.shields.io/badge/NEXUS-v0.3.0-820F1A?style=flat-square)](CHANGELOG.md)
[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![License](https://img.shields.io/badge/License-Apache_2.0-808080?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-189_passing-2ea44f?style=flat-square)](sdk/python/tests)

*Cyber Strategy Institute reference implementation for governed agent-to-agent and agent-to-tool enforcement*

</div>

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [MCP Profile](../00-cross-pillar/cp5_mcp_server_security.md) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

**Previous:** [← AISM](../AISM/) | **Next:** [Gateway / Runtime Enforcement →](../gateway/)

---

## Role in AI SAFE² v3.1

**AI SAFE² is the governance and requirements standard. NEXUS is Cyber Strategy Institute's first-party reference implementation.**

NEXUS demonstrates one way to enforce AI SAFE² requirements across:

- **east-west agent-to-agent traffic**: identity, delegation, lineage, policy, revocation, audit;
- **agent-to-tool traffic**: MCP/tool capability grants, provenance, state binding, returned-content trust, authorization evidence.

Organizations do not have to deploy NEXUS to claim AI SAFE² conformance. They must demonstrably satisfy the applicable AI SAFE² controls and produce the required independently reconstructable evidence.

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                            NEXUS-A2A v0.3                                  │
├───────────┬─────────────────────────────────────────────────────────────────┤
│ L6        │ Governance Plane       Constitutional constraints, amendments   │
│ L5        │ Economic Governance    Compute/accounting ceilings              │
│ L4        │ Memory and Context     Memory Vaccine, provenance, AgBOM        │
│ L3        │ Policy Enforcement     Guardian, OPA, AISM invariants           │
│ L2        │ Identity + Delegation  AIM, VCC, scoped authority, lineage      │
│ L1        │ Transport Security     mTLS, workload identity, crypto binding  │
├───────────┴─────────────────────────────────────────────────────────────────┤
│ Bridges / adapters: A2A | ACS | MCP | OpenAI | LangChain | CrewAI | n8n    │
└─────────────────────────────────────────────────────────────────────────────┘
```

NEXUS wraps the user's stack. It does not replace the model, agent framework, or tool protocol.

---

## What NEXUS Implements

| Security property | NEXUS mechanism |
|---|---|
| Verified agent/workload identity | AIM + DID and supported workload-attestation mechanisms |
| Delegation scope attenuation | VCC and monotonic scope constraints |
| Memory provenance and drift controls | Memory Vaccine and provenance records |
| Per-action policy enforcement | Guardian + OPA policies |
| Non-repudiable operational receipts | NOR and OTel/OCSF-compatible evidence |
| Dynamic agent supply-chain inventory | AgBOM |
| Fail-closed enforcement | Guardian/gateway decision paths |
| Protocol/tool governance | Bridges and the v3.1 MCP adapter contract |

---

## v3.1 Enforcement Planes

| Plane | NEXUS role | Status |
|---|---|---|
| **East-west: agent to agent** | Identity, delegation, authority, lineage, evidence | v0.3 implementation |
| **Agent-to-tool: MCP/tool** | CP.5.MCP enforcement contract and adapter path | v3.1 adapter contract present; production implementation still required |
| **North-south: model/provider** | Integrates with AI SAFE² gateway/runtime controls | Reference integration path |

### MCP status is intentionally explicit

The `NEXUS/adapters/mcp/adapter.py` file added for AI SAFE² v3.1 is a **fail-closed interface skeleton**. Unimplemented methods raise rather than silently permit traffic.

It must not be described as production-ready until the authorization, provenance, state-handle, catalog, replay, and MCP-19 resource/audience enforcement paths are implemented and tested.

See [NEXUS MCP adapter](./adapters/mcp/) and [CP.5.MCP](../00-cross-pillar/cp5_mcp_server_security.md).

---

## Install

```bash
# Core SDK
pip install nexus-a2a-sdk

# Full production dependencies where supported
pip install "nexus-a2a-sdk[full]"
```

From source:

```bash
cd NEXUS/sdk/python
pip install -e .
```

---

## Quick Start

### Guardian: enforce before execution

```python
from nexus_sdk.guardian import GuardianPolicy, NEXUSGuardianClient, build_tool_call_step

policy = GuardianPolicy(blocked_argument_patterns=["../", "../../"])
guardian = NEXUSGuardianClient(
    inline_policy=policy,
    fail_mode=NEXUSGuardianClient.FAIL_CLOSED,
)

step = build_tool_call_step(
    agent_did="did:nexus:agent:my-agent",
    spiffe_id="spiffe://nexus.local/agent/my-agent",
    tool_name="read_file",
    tool_arguments={"path": "../../etc/passwd"},
    act_tier=2,
)

verdict = guardian.evaluate(step)
```

### NOR: produce attributable evidence

```python
from nexus_sdk.otel import build_tool_call_nor, nor_to_otel_attributes

nor = build_tool_call_nor(
    agent_did="did:nexus:agent:my-agent",
    spiffe_id="spiffe://nexus.local/agent/my-agent",
    tool_name="read_file",
    outcome=verdict.decision,
)

attrs = nor_to_otel_attributes(nor)
```

### Memory Vaccine: govern persistence

AI SAFE² v3.1 uses the canonical governance vocabulary:

- `request`;
- `handle_scoped`;
- `durable`.

Older NEXUS APIs may still expose `SESSION`, `CROSS_SESSION`, or `PERMANENT` as compatibility aliases during migration. Those legacy names must not be treated as protocol identity or authorization boundaries.

```python
from nexus_sdk.memory import MemoryVaccine

mv = MemoryVaccine(
    "did:nexus:agent:my-agent",
    "research assistant",
    use_stub_embeddings=True,
)
```

### AgBOM: track the agent supply chain

```python
from nexus_sdk.agbom import AgBOMManager

agbom = AgBOMManager("did:nexus:agent:my-agent")
agbom.discover_mcp_server(
    "filesystem-mcp",
    "http://localhost:3000",
    version="1.0",
)

chain_ok, violations = agbom.verify_chain_integrity()
```

---

## AISM Invariants

NEXUS encodes architectural invariants as enforceable policy. The v3.1 interpretation is:

| Invariant | Requirement |
|---|---|
| **I-1 Authenticated Borders** | Verify the principal/workload at governed boundaries |
| **I-2 Monotonic Scope** | Delegated authority narrows or expires; it does not silently expand |
| **I-3 Memory Provenance** | Governed persistent writes require attributable provenance and policy context |
| **I-4 Physical/External Kill Path** | High-autonomy deployments retain an independently operable stop path |
| **I-5 Owner of Record** | Every governed agent has accountable human ownership |
| **I-6 Bias as Security Signal** | Material behavioral drift can be treated as a security event, not merely a quality metric |

Policy files:

- [`opa/nexus-authz.rego`](opa/nexus-authz.rego)
- [`opa/nexus-aism-invariants.rego`](opa/nexus-aism-invariants.rego)

---

## AI SAFE² v3.1 Alignment

NEXUS is evaluated as an implementation against AI SAFE². The framework is not considered proven merely because NEXUS implements a control.

Key v3.1 expectations include:

- enforcement-plane scoping;
- protocol-independent governance constructs;
- verified principal and delegation evidence;
- request/handle/durable persistence semantics;
- explicit MCP `2026-07-28` profile handling;
- MCP-19 intended-resource/audience validation or equivalent evidenced binding;
- fail-closed behavior where enforcement is incomplete.

The existing scoring utility remains an implementation checker and should not be treated as independent framework validation.

---

## Protocol and Integration Status

| Integration | Status |
|---|---|
| ACS Guardian / AOS JSON-RPC | v0.3 supported |
| Agent-to-agent bridge paths | v0.3 supported |
| OpenAI/function calling bridge | Existing implementation |
| LangChain / LangGraph | Existing implementation |
| CrewAI | Existing implementation |
| n8n | Existing implementation |
| REST bridge | Existing implementation |
| MCP legacy bridge behavior | Existing compatibility path |
| **MCP `2026-07-28` v3.1 enforcement adapter** | **Contract/scaffolding, not production-ready** |

This table intentionally separates existing bridge code from the new v3.1 MCP enforcement contract.

---

## Repository Map

```text
NEXUS/
├── adapters/
│   └── mcp/                    v3.1 agent-to-tool adapter contract
├── sdk/python/nexus_sdk/       Core SDK
├── sdk/python/tests/           SDK tests
├── opa/                        Authorization and AISM invariant policies
├── schemas/                    AIM, NOR, AgBOM, Guardian schemas
├── docker/                     Reference deployment assets
├── examples/                   Gateway, bridge, and personal-agent examples
├── governance/                 Governance charter and draft protocol work
└── compliance/scoring/         NEXUS implementation scoring
```

---

## Governance and Licensing

NEXUS is licensed under **Apache 2.0** where designated in the NEXUS subtree. This differs from the broader AI SAFE² repository licensing model, which uses MIT for code and CC BY-SA 4.0 for framework/documentation material unless a subtree states otherwise.

See:

- [`governance/GOVERNANCE.md`](governance/GOVERNANCE.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)
- [`SECURITY.md`](SECURITY.md)
- [`LICENSE`](LICENSE)

---

## 🔗 Navigation

| Previous | Current | Next |
|---|---|---|
| [AISM](../AISM/) | **NEXUS** | [Gateway](../gateway/) |

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [MCP Profile](../00-cross-pillar/cp5_mcp_server_security.md) | [Challenge Lab](../challenges/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

*AI SAFE² v3.1 reference implementation · NEXUS v0.3 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com)*
