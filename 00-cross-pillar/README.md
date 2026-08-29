# Cross-Pillar Governance Layer
### ⚙️ The Governance OS

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Layer](https://img.shields.io/badge/Layer-Cross--Pillar-820F1A?style=flat-square)](./README.md)
[![Core](https://img.shields.io/badge/Core-CP.1--CP.10-808080?style=flat-square)](#cross-pillar-controls)
[![MCP](https://img.shields.io/badge/MCP-2026--07--28-820F1A?style=flat-square)](./cp5_mcp_server_security.md)

[Framework Home](../README.md) | [Pillars](../01-sanitize-isolate/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

**Previous:** [← Pillar 5: Evolve & Educate](../05-evolve-educate/README.md) | **Next:** [AISM →](../AISM/)

---

## 🎯 The Problem. The Realization. The Solution.

**Problem:** Operational controls are not enough when autonomous systems can delegate authority, spawn agents, call external tools, preserve state, cross protocol boundaries, or take actions whose consequences exceed the scope of one pillar.

**Realization:** Agentic governance needs a layer that defines authority, accountability, risk, evidence, emergency control, delegation, replication, and protocol-specific security across the entire system.

**Solution:** The Cross-Pillar Governance Layer is the governance operating system for AI SAFE². **CP.1 through CP.10 are the core cross-pillar controls introduced in v3.0 and retained in v3.1.** Version 3.1 strengthens CP.5 by formalizing protocol-independent security profiles and the three enforcement planes: north-south, east-west, and agent-to-tool.

> **What you get:** A common governance contract across the five operational pillars, named human authority for autonomous deployments, bounded delegation and replication, protocol-aware security profiles, and evidence that can be independently reconstructed.

---

## v3.1 Governance Model

### Three enforcement planes

| Plane | Traffic | Primary governance question | Reference path |
|---|---|---|---|
| **North-south** | Agent to model/provider | What can cross the provider boundary, under what policy and economic ceiling? | Gateway/runtime controls |
| **East-west** | Agent to agent | Who delegated what authority, to whom, for how long, and with what lineage? | NEXUS A2A reference implementation |
| **Agent-to-tool** | Agent to MCP/tool server | Which verified principal may invoke which capability, and how is returned content trusted? | CP.5.MCP + NEXUS MCP adapter contract |

### Protocol-independence rule

> **A CP.5 profile MUST NOT bind a control to a construct owned by the protocol it profiles.**

Governance binds to framework-owned constructs such as verified principals, capability grants, delegation chains, provenance baselines, policy context, trust-establishment events, and state handles. This prevents a protocol lifecycle change from silently invalidating a governance claim.

---

## Cross-Pillar Controls

| Control | Name | Priority | Governs |
|---|---|---:|---|
| **CP.1** | Agent Failure Mode Taxonomy | 🔴 CRITICAL | Failure classification across pillars, cognitive surfaces, persistence scope, and remediation path |
| **CP.2** | Adversarial ML Threat Model Integration | 🔴 CRITICAL | Threat mapping, temporal behavior, and adversarial context |
| **CP.3** | ACT Capability Tiers 1-4 | 🔴 CRITICAL | Autonomy classification and control scaling |
| **CP.4** | Agentic Control Plane Governance | 🔴 CRITICAL | Identity, authorization, delegation, orchestration, runtime trust |
| **CP.5** | Platform and Protocol Security Profiles | 🟠 HIGH | Platform-specific and protocol-specific enforcement profiles |
| **CP.6** | AI Incident Feedback Loop Integration | 🟠 HIGH | Incident-informed control review and continuous improvement |
| **CP.7** | Deception & Active Defense Layer | 🟠 HIGH | Canaries, honeypots, and adversarial detection assets |
| **CP.8** | Catastrophic Risk Threshold Controls | 🔴 CRITICAL | Mandatory stop conditions and emergency suspension |
| **CP.9** | Agent Replication Governance | 🔴 CRITICAL | Spawn authority, lineage, descendant revocation, delegation depth |
| **CP.10** | HEAR Doctrine | 🔴 CRITICAL | Named Human Ethical Agent of Record and unilateral kill authority |

### CP.11 Unbiased AI Standard

**CP.11 is a compliance overlay module, not an additional core framework control for purposes of the 161-control AI SAFE² core count.** It composes and tests existing controls across AI SAFE², NEXUS, and the Cognitive Sovereignty Framework against Unbiased AI procurement and due-diligence requirements.

See the full module: [Unbiased AI Standard](./unbiased-ai/README.md).

---

## CP.1: Agent Failure Mode Taxonomy

Every material agentic incident should be classified in a way that points to the correct remediation layer.

### Canonical v3.1 persistence vocabulary

Use:

- `request`: effect is limited to the current request or interaction;
- `handle_scoped`: effect persists only through an explicitly governed state handle;
- `durable`: effect persists beyond a request or handle lifecycle and requires durable-state governance.

Legacy terms such as `session`, `cross_session`, and `permanent` may be accepted as compatibility aliases during migration, but they are not the canonical governance boundary in v3.1.

Recommended incident dimensions include:

- `cognitive_surface = model | memory | both`;
- `persistence_scope = request | handle_scoped | durable`;
- affected principal or agent identity;
- delegation lineage;
- enforcement plane;
- policy and evidence references.

---

## CP.2: Adversarial ML Threat Model Integration

ACT-2 and above deployments maintain a threat model with temporal behavior rather than treating every attack as an instantaneous event.

Example temporal classifications include:

- `immediate`;
- `delayed_days`;
- `delayed_weeks`;
- `chronic`.

This supports investigation of latent prompt poisoning, slow memory conditioning, long-horizon RAG corruption, protocol drift, and delayed supply-chain compromise.

---

## CP.3: Agent Capability Tiers

| Tier | Operating model | Governance expectation |
|---|---|---|
| **ACT-1** | Assisted | Human reviews consequential outputs before action |
| **ACT-2** | Supervised | Agent acts within bounded workflows and human checkpoints |
| **ACT-3** | Autonomous | Agent acts within a defined authority envelope with post-action review and HEAR coverage |
| **ACT-4** | Orchestrator | Agent controls agents or materially broader systems; full control-plane, replication, catastrophic-risk, and HEAR requirements apply |

Higher tiers inherit lower-tier requirements unless an explicit profile states otherwise.

---

## CP.4: Agentic Control Plane Governance

CP.4 makes identity, authorization, delegation, orchestration, and runtime trust explicit governance objects.

Minimum evidence for ACT-3/ACT-4 should include:

- verified principal or agent identity;
- `owner_of_record`;
- ACT tier;
- capability grants and restrictions;
- delegation lineage;
- policy version;
- revocation status;
- HEAR assignment where required.

Boards and security leaders should be able to measure owner coverage, high-tier agent concentration, machine-to-human identity ratios, and control-plane conformance without reconstructing those facts from application logs.

---

## CP.5: Platform and Protocol Security Profiles

CP.5 translates the framework into version-pinned profiles for specific platforms and protocols while preserving the protocol-independence rule.

### CP.5.MCP: MCP Server Security Profile

The **canonical v3.1 MCP profile contains MCP-1 through MCP-19** and is aligned to MCP `2026-07-28`, with `2025-11-25` retained as a legacy compatibility binding.

Key v3.1 changes include:

- no governance dependency on `Mcp-Session-Id`;
- `server/discover` is optional and not a conformance presence requirement;
- extension capability negotiation;
- header/body assertion integrity;
- state-handle lifecycle and principal binding;
- MRTR request/response integrity and replay resistance;
- catalog-cache provenance revalidation;
- authorization-chain, intended-resource/audience, redirect, metadata, and SSRF validation.

**Do not maintain a second embedded copy of the MCP control matrix on this page.** The canonical specification is:

[CP.5.MCP v3.1: MCP Server Security Profile](./cp5_mcp_server_security.md)

Machine-readable profile data is maintained at:

[`skills/mcp/data/mcp-profile-v3.1.json`](../skills/mcp/data/mcp-profile-v3.1.json)

NEXUS provides CSI's first-party reference implementation path for agent-to-tool enforcement. Alternative implementations may conform when they satisfy the applicable controls and produce independently reconstructable evidence.

---

## CP.6: AI Incident Feedback Loop Integration

External and internal incidents must feed back into the framework on a defined cadence.

Recommended mechanisms include:

- periodic external incident review;
- a time-bounded Incident-Informed Control Review for materially relevant incidents;
- an internal Agentic Incident Registry;
- traceability from incident to control, test, policy, and remediation change.

---

## CP.7: Deception & Active Defense Layer

AI-specific active defense may include:

- canary documents in RAG corpora;
- honeypot tool endpoints;
- synthetic credentials or artifacts that should never be used legitimately;
- telemetry that converts unexpected interaction with those assets into evidence and an escalation event.

Deception assets must themselves be governed so that they do not become uncontrolled production behavior.

---

## CP.8: Catastrophic Risk Threshold Controls

ACT-3 and ACT-4 deployments define conditions that require emergency suspension regardless of ordinary business-continuity preference.

Thresholds should cover the deployment's actual consequence surface, including unauthorized state change, uncontrolled replication, destructive tool use, material economic harm, safety impact, protocol supply-chain compromise, or loss of effective human control.

---

## CP.9: Agent Replication Governance

Replication changes identity, permission, execution, and audit assumptions simultaneously.

CP.9 requires:

- explicitly declared spawn authority;
- narrowed descendant capabilities;
- cryptographic or otherwise verifiable lineage;
- bounded delegation depth and lifetime;
- dynamic inventory of active descendants;
- revocation that reaches the full descendant tree;
- evidence connecting each descendant action to its originating authority.

---

## CP.10: HEAR Doctrine

Every ACT-3 and ACT-4 deployment requires a named **Human Ethical Agent of Record (HEAR)** with real authority to halt the governed deployment.

For Class-H actions, the system must pause, present the real-world consequence in understandable terms, obtain valid authorization from the HEAR or designated authority, record the authorization, and only then execute.

If required authorization infrastructure is unavailable, the action fails closed.

---

## CP.11: Unbiased AI Standard

The UAS module defines an auditable compliance surface for Unbiased AI obligations in procurement and due diligence. It includes bias taxonomy, tests, evidence expectations, attestation, and cross-framework mappings.

Because the module composes controls from multiple systems, its module-level control count must not be added to the 161 AI SAFE² core-control total as though those were all new independent core controls.

Full module: [00-cross-pillar/unbiased-ai/](./unbiased-ai/README.md)

---

## Cross-Pillar GRC Mapping

| Framework | Representative CP controls | Governance contribution |
|---|---|---|
| EU AI Act | CP.3, CP.8, CP.10 | Risk scaling, emergency thresholds, human oversight |
| NIST AI RMF | CP.1-CP.6, CP.10 | GOVERN, MAP, MEASURE, MANAGE evidence |
| NIST CSF 2.0 | CP.3, CP.4, CP.6, CP.8 | Governance, identity, incident feedback, response thresholds |
| ISO/IEC 42001 | CP.1-CP.8, CP.10 | AI management-system governance and oversight |
| SOC 2 | CP.4, CP.6, CP.10 | Access, operations, incident response, accountability |
| OWASP Agentic guidance | CP.4, CP.5, CP.9, CP.10 | Identity, protocol/tool risk, replication, human authority |
| Zero Trust | CP.4, CP.5, CP.9 | Principal verification, least privilege, delegation and revocation |

Mappings are evidence reuse aids, not substitutes for an organization's independent applicability or certification determination.

---

## Getting Started

Implement in this order for the fastest governance baseline:

1. Classify deployed agents by ACT tier (CP.3).
2. Assign `owner_of_record` and verified identities (CP.4).
3. Designate HEAR coverage for ACT-3/ACT-4 deployments (CP.10).
4. Define catastrophic-risk thresholds (CP.8).
5. Audit replication and delegation capabilities (CP.9).
6. Apply platform/protocol profiles, including CP.5.MCP where MCP is used.
7. Establish incident-to-control feedback (CP.6).

Current implementation resources: [AI SAFE² Toolkit](https://cyberstrategyinstitute.com/ai-safe2/)

---

## 🔗 Navigation

| Previous | Current | Next |
| :--- | :--- | :--- |
| [Pillar 5: Evolve & Educate](../05-evolve-educate/README.md) | **Cross-Pillar Governance** | [AISM](../AISM/) |

[Framework Home](../README.md) | [Pillar 1](../01-sanitize-isolate/README.md) | [Pillar 2](../02-audit-inventory/README.md) | [Pillar 3](../03-fail-safe-recovery/README.md) | [Pillar 4](../04-engage-monitor/README.md) | [Pillar 5](../05-evolve-educate/README.md)

[NEXUS](../NEXUS/) | [MCP Profile](./cp5_mcp_server_security.md) | [Research](../research/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/) | [Toolkit](https://cyberstrategyinstitute.com/ai-safe2/)

---

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
