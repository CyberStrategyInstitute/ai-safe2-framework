# NEXUS-A2A v0.4

**Non-repudiable, Extensible, eXecutive-Unified, Sovereign Agent-to-Agent Governance**

[![NEXUS](https://img.shields.io/badge/NEXUS-v0.4.0-820F1A?style=flat-square)](CHANGELOG.md)
[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![License](https://img.shields.io/badge/License-Apache_2.0-808080?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-298_passing-2ea44f?style=flat-square)](sdk/python/tests)

*Cyber Strategy Institute reference implementation for governed agent-to-agent, agent-to-tool, and agent-to-payment enforcement*

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM) | [MCP Profile](../00-cross-pillar/cp5_mcp_server_security.md) | [**Payments Profile**](payments/README.md) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

**Previous:** [← AISM](../AISM) | **Next:** [Gateway / Runtime Enforcement →](../gateway)

---

## Role in AI SAFE² v3.1

**AI SAFE² is the governance and requirements standard. NEXUS is Cyber Strategy Institute's first-party reference implementation.**

NEXUS demonstrates one way to enforce AI SAFE² requirements across:

- **east-west agent-to-agent traffic**: identity, delegation, lineage, policy, revocation, audit;
- **agent-to-tool traffic**: MCP/tool capability grants, provenance, state binding, returned-content trust, authorization evidence;
- **agent-to-payment traffic** *(new in v0.4)*: mandate integrity, runtime-bound authorization, aggregate economic containment, measured revocation, dispute-grade evidence.

Organizations do not have to deploy NEXUS to claim AI SAFE² conformance. They must demonstrably satisfy the applicable AI SAFE² controls and produce the required independently reconstructable evidence.

---

## What changed in v0.4

v0.4 adds the **agent-to-payment enforcement plane** as [CP.5.APAY](payments/README.md), the Agentic Payments Integrity Profile.

The reasoning is short. The agentic payments ecosystem is standardizing fast, and it is standardizing around two questions: *is this a registered agent* (Visa TAP, Mastercard Agent Pay, both on Web Bot Auth) and *did a human approve this purchase* (AP2, contributed to the FIDO Alliance in April 2026). Both are being answered well.

Neither is the question that decides whether money stays where it belongs. That question is whether the workload holding a valid credential is still running the software that was approved — and every one of those protocols assumes the signing host is trustworthy without requiring proof of it. An attacker who owns the agent host inherits its identity, registrations and mandates intact, and every signature they produce verifies correctly, because it is correct.

> Identity proves which agent arrived.
> Mandates prove what authority was granted.
> NEXUS proves whether this measured workload may still use that authority for this transaction, at this moment — and stops the entire authority tree when it may not.

Two AISM invariants are added alongside the existing six: **I-7 Runtime-Bound Authority** and **I-8 Aggregate Economic Containment**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            NEXUS-A2A v0.4                                   │
├───────────┬─────────────────────────────────────────────────────────────────┤
│ L7        │ Value Integrity        CP.5.APAY: mandates, runtime binding,    │
│           │                        containment, revocation, PTR evidence    │
│ L6        │ Governance Plane       Constitutional constraints, amendments   │
│ L5        │ Economic Governance    Compute/accounting ceilings              │
│ L4        │ Memory and Context     Memory Vaccine, provenance, AgBOM        │
│ L3        │ Policy Enforcement     Guardian, OPA, AISM invariants           │
│ L2        │ Identity + Delegation  AIM, VCC, scoped authority, lineage      │
│ L1        │ Transport Security     mTLS, workload identity, crypto binding  │
├───────────┴─────────────────────────────────────────────────────────────────┤
│ Bridges / adapters: A2A | ACS | MCP | OpenAI | LangChain | CrewAI | n8n      │
│ Payment bindings:   AP2 | x402 | Visa TAP | Agent Pay | KYA-OS  (contracts)  │
└─────────────────────────────────────────────────────────────────────────────┘
```

NEXUS wraps the user's stack. It does not replace the model, agent framework, tool protocol, wallet, or payment rail.

---

## What NEXUS Implements

| Security property                    | NEXUS mechanism                                         |
| ------------------------------------ | ------------------------------------------------------- |
| Verified agent/workload identity     | AIM + DID and supported workload-attestation mechanisms |
| Delegation scope attenuation         | VCC and monotonic scope constraints                     |
| Memory provenance and drift controls | Memory Vaccine and provenance records                   |
| Per-action policy enforcement        | Guardian + OPA policies                                 |
| Non-repudiable operational receipts  | NOR and OTel/OCSF-compatible evidence                   |
| Dynamic agent supply-chain inventory | AgBOM                                                   |
| Fail-closed enforcement              | Guardian/gateway decision paths                         |
| Protocol/tool governance             | Bridges and the v3.1 MCP adapter contract               |
| **Runtime-bound value authorization** | **Payment Integrity Gateway + `RuntimeMeasurement`**   |
| **Aggregate economic containment**   | **Authority graph subtree exposure accounting**         |
| **Measured revocation**              | **Revocation epochs + `exposure_after_revocation`**     |
| **Dispute-grade payment evidence**   | **PTR, hash-chained, selectively disclosed**            |

---

## Enforcement Planes

| Plane                           | NEXUS role                                         | Status                                                                  |
| ------------------------------- | -------------------------------------------------- | ----------------------------------------------------------------------- |
| **East-west: agent to agent**   | Identity, delegation, authority, lineage, evidence | v0.3 implementation                                                     |
| **Agent-to-tool: MCP/tool**     | CP.5.MCP enforcement contract and adapter path     | v3.1 adapter contract present; production implementation still required |
| **Agent-to-payment: value**     | CP.5.APAY mandate, runtime, containment, evidence  | **v0.4 core and narrow reference adapters implemented and tested**      |
| **North-south: model/provider** | Integrates with AI SAFE² gateway/runtime controls  | Reference integration path                                              |

### MCP status is intentionally explicit

The `NEXUS/adapters/mcp/adapter.py` file added for AI SAFE² v3.1 is a **fail-closed interface skeleton**. Unimplemented methods raise rather than silently permit traffic.

It must not be described as production-ready until the authorization, provenance, state-handle, catalog, replay, and MCP-19 resource/audience enforcement paths are implemented and tested.

See [NEXUS MCP adapter](adapters/mcp) and [CP.5.MCP](../00-cross-pillar/cp5_mcp_server_security.md).

### Payment status is intentionally explicit

The CP.5.APAY **core** and its narrow reference adapters are implemented and tested. See the [adapter guide](payments/ADAPTER-GUIDE.md) for supported profiles, integration boundaries, and verification commands.

The **rail bindings** in `nexus_sdk/payments/adapters.py` (AP2, x402, Visa TAP, Mastercard Agent Pay, KYA-OS) are fail-closed contracts. Every enforcement method raises. They are published as contracts rather than stubs because each requires conformance testing against a live counterparty before it can be claimed, and a stub returning success would let a deployment believe it has binding it does not have.

The default credential broker is `NullCredentialBroker`, which **refuses every signing request**. An unconfigured payment path does not move money. Replacing that default with a permissive stub is the single most damaging change available in this codebase.

No production assurance is claimed. See the [MVP acceptance gates](payments/README.md#mvp-acceptance-gates).

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
cd NEXUS
pip install -e .
```

> **v0.4 packaging fix.** Prior releases declared an invalid `build-backend`, which made the package uninstallable from source. Corrected to `setuptools.build_meta`.

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

### Payments: authority that narrows and cannot be widened

```python
from nexus_sdk.payments import AuthorityGraph, MandateCompiler, Money

compiler = MandateCompiler()
mandate = compiler.compile(
    "Buy cloud capacity from approved vendors, up to $500 a time",
    explicit={"allowed_merchants": {"vendor-a"},
              "max_aggregate": Money.parse("5000.00")},
)
grant = compiler.issue(mandate, principal_id="principal-1",
                       rendering=compiler.render(mandate))

graph = AuthorityGraph()
graph.register_root(grant)

graph.delegate(grant.authority_grant_id, max_transaction=Money.parse("50.00"))   # ok
graph.delegate(grant.authority_grant_id, max_transaction=Money.parse("5000.00"))
# AttenuationError: delegation would widen parent authority on: max_transaction
```

Open-ended instructions do not become numbers:

```python
compiler.compile("spend whatever we need on infrastructure").unresolved
# [Ambiguity(axis='max_transaction', detail='instruction contains open-ended
#  spend language; a ceiling must be set explicitly', resolution=None)]
```

See [payments/README.md](payments/README.md) for the full sequence.

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

AI SAFE² v3.1 uses the canonical governance vocabulary: `request`, `handle_scoped`, `durable`.

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
agbom.discover_mcp_server("filesystem-mcp", "http://localhost:3000", version="1.0")

chain_ok, violations = agbom.verify_chain_integrity()
```

---

## AISM Invariants

NEXUS encodes architectural invariants as enforceable policy. The v0.4 interpretation is:

| Invariant                           | Requirement                                                                               |
| ----------------------------------- | ----------------------------------------------------------------------------------------- |
| **I-1 Authenticated Borders**       | Verify the principal/workload at governed boundaries                                      |
| **I-2 Monotonic Scope**             | Delegated authority narrows or expires; it does not silently expand                       |
| **I-3 Memory Provenance**           | Governed persistent writes require attributable provenance and policy context             |
| **I-4 Physical/External Kill Path** | High-autonomy deployments retain an independently operable stop path                      |
| **I-5 Owner of Record**             | Every governed agent has accountable human ownership                                      |
| **I-6 Bias as Security Signal**     | Material behavioral drift can be treated as a security event, not merely a quality metric |
| **I-7 Runtime-Bound Authority** *(new)* | Authority to take a consequential action binds to a fresh measurement of the workload exercising it, not only to the identity presenting it |
| **I-8 Aggregate Economic Containment** *(new)* | Consumable authority aggregates across the authority tree; every descendant's consumption counts against every ancestor's ceiling |

Policy files:

- [`opa/nexus-authz.rego`](opa/nexus-authz.rego)
- [`opa/nexus-aism-invariants.rego`](opa/nexus-aism-invariants.rego)
- [`opa/nexus-apay.rego`](opa/nexus-apay.rego) *(new)*

The payment policy and the in-process `TransactionFirewall` are fed from one input contract (`nexus_sdk/payments/opa_input.py`), and [`tests/test_apay_opa_contract.py`](sdk/python/tests/test_apay_opa_contract.py) fails if the Rego references an input path nothing supplies. Two implementations of one rule set drift, and drift in a policy engine is silent: the two disagree only on the transactions that matter.

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

| Integration                                   | Status                                         |
| --------------------------------------------- | ---------------------------------------------- |
| ACS Guardian / AOS JSON-RPC                   | v0.3 supported                                 |
| Agent-to-agent bridge paths                   | v0.3 supported                                 |
| OpenAI/function calling bridge                | Existing implementation                        |
| LangChain / LangGraph                         | Existing implementation                        |
| CrewAI                                        | Existing implementation                        |
| n8n                                           | Existing implementation                        |
| REST bridge                                   | Existing implementation                        |
| MCP legacy bridge behavior                    | Existing compatibility path                    |
| **MCP `2026-07-28` v3.1 enforcement adapter** | **Contract/scaffolding, not production-ready** |
| **CP.5.APAY core and reference adapters**      | **v0.4 implemented and adversarially tested**  |
| **Identity normalization (Entra/KYA-OS/SPIFFE/Web Bot Auth)** | **v0.4 implemented**           |
| **AP2 binding**                               | **Contract only, not implemented**             |
| **x402 SafePay Exact binding** (`X402V2ExactEVMUSDCBinding`) | **Narrow structural binding implemented; shadow mode only, no live facilitator or chain verification** |
| **Visa TAP / Web Bot Auth binding**           | **Contract only, not implemented**             |
| **Mastercard Agent Pay binding**              | **Contract only, not implemented**             |
| **KYA-OS binding**                            | **Contract only, not implemented**             |

This table intentionally separates existing bridge code from enforcement contracts that are not yet implemented.

---

## Repository Map

```
NEXUS/
├── adapters/
│   └── mcp/                    v3.1 agent-to-tool adapter contract
├── payments/                   CP.5.APAY profile, threat model, controls, challenge lab
├── sdk/python/nexus_sdk/       Core SDK
│   └── payments/               Payment Integrity Gateway
├── sdk/python/tests/           SDK tests (298 passing)
├── opa/                        Authorization, AISM invariant, and APAY policies
├── schemas/                    AIM, NOR, AgBOM, Guardian, APAY grant, APAY PTR schemas
├── docker/                     Reference deployment assets
├── examples/                   Gateway, bridge, and personal-agent examples
├── governance/                 Governance charter and draft protocol work
└── compliance/scoring/         NEXUS implementation scoring
```

---

## Testing

```bash
cd NEXUS
pip install -e ".[dev]"
pytest sdk/python/tests -q
```

The payment suite is structured so that a control with only a happy-path test does not count as a control: every APAY control has at least one test proving it denies what it claims to deny, and the `TestHonesty` class fails if anyone makes a fail-closed default permissive. Run the current suite rather than relying on a documentation test count.

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
| -------- | ------- | ---- |
| [AISM](../AISM) | **NEXUS** | [Payments Profile](payments/README.md) → [Gateway](../gateway) |

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM) | [MCP Profile](../00-cross-pillar/cp5_mcp_server_security.md) | [Payments Profile](payments/README.md) | [Challenge Lab](../challenges) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

*AI SAFE² v3.1 reference implementation · NEXUS v0.4 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com)*
