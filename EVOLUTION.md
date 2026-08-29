# AI SAFE² Framework Evolution History

This document outlines the strategic evolution of the AI SAFE² framework from a conceptual foundation to a production-oriented governance and runtime-enforcement system.

---

## Version History

| Version | Released | Framework Controls | Frameworks | Primary focus |
| :--- | :--- | :--- | :--- | :--- |
| **v3.1** | August 2026 | **161** | 32 | MCP `2026-07-28`, protocol-independent governance, three enforcement planes |
| **v3.0** | April 2026 | **161** | 32 | Swarm governance, production evidence, CP.1 through CP.10 |
| v2.1 | November 2025 | 128 | 14 | Agentic and distributed governance |
| v2.0 | October 2025 | 99 | Core | Enterprise operations |
| v1.0 | June 2025 | 10 | Initial | Foundational concepts |

---

<a id="v31"></a>
## Version 3.1: Protocol Governance and Enforcement Planes Edition (Current)

**Released:** August 2026  
**Core concept:** Governance must survive protocol change.

Version 3.1 responds to a structural change in the Model Context Protocol. MCP `2026-07-28` makes the core protocol substantially more stateless, removes the required `initialize`/`initialized` handshake and `Mcp-Session-Id`, adds optional `server/discover`, introduces cacheable catalogs and protocol extensions, and strengthens the authorization model.

The security implication is larger than a version bump. A governance framework cannot safely bind identity, authorization, memory, or evidence to protocol-owned lifecycle concepts that may disappear in the next protocol revision. AI SAFE² v3.1 therefore moves the governance boundary to framework-owned constructs.

### Governing design rule

> A CP.5 profile MUST NOT bind a control to a construct owned by the protocol it profiles.

The canonical governance objects are now verified principals, capability grants, delegation chains, provenance baselines, state handles, trust-establishment events, policy decisions, and independently reconstructable evidence.

### Three enforcement planes

v3.1 makes three distinct enforcement planes explicit:

| Plane | Traffic | Primary governance concern |
|---|---|---|
| North-south | Agent to model provider | Content, policy, consumption, and spend |
| East-west | Agent to agent | Identity, delegation, lineage, and authority |
| Agent-to-tool | Agent to MCP server or tool | Tool authorization, provenance, output trust, and economic amplification |

The three planes remain separate enforcement points but use a common policy vocabulary, principal model, and evidence model.

### CP.5.MCP: 13 to 19 profile controls

The MCP profile expands from 13 to 19 sub-controls while the overall AI SAFE² framework remains **161 controls**.

The six new MCP profile controls are:

| Control | Focus |
|---|---|
| MCP-14 | Extension capability negotiation |
| MCP-15 | Header/body assertion integrity |
| MCP-16 | State-handle binding and lifecycle |
| MCP-17 | MRTR round-trip integrity and replay resistance |
| MCP-18 | Catalog-cache integrity and provenance revalidation |
| MCP-19 | Authorization-chain integrity, intended resource/audience validation, and SSRF boundaries |

These are profile-level controls under CP.5. They do not change the top-level 161-control count.

### NEXUS relationship

AI SAFE² specifies what must be governed and enforced. NEXUS provides Cyber Strategy Institute's first-party reference implementation across the agent-to-agent and agent-to-tool planes. Organizations may use NEXUS or another implementation that demonstrably satisfies the applicable controls and required evidence.

The v3.1 NEXUS MCP adapter defines a fail-closed interface contract. Unimplemented methods raise rather than silently allowing traffic. It is an implementation contract, not a claim that the adapter is production-ready.

### Compatibility

MCP `2025-11-25` remains supported as a legacy binding for twelve months. Legacy `Mcp-Session-Id` values are treated as principal-scoped state handles, not identity or authorization boundaries.

`server/discover` is optional in MCP `2026-07-28` and is not required for AI SAFE² conformance.

### MCP-19 authorization boundary

Opaque static bearer tokens do not contain an audience claim. They therefore do not, by themselves, establish MCP-19 audience-validation conformance. A deployment must validate the intended resource or provide equivalent independently evidenced resource binding before claiming the control.

### Challenge Lab synchronization

Challenge 001 remains falsification-first. The framework and its reference implementation are subjects of the experiment, not sources of their own proof. v3.1 further requires that claims be scoped to the enforcement planes actually exercised. Successful east-west governance does not automatically validate the MCP/tool plane or north-south provider plane.

Material normative changes to the framework, protocol profile, implementation, policy, or grader after preregistration require a new preregistration version before confirmatory evidence is pooled.

---

<a id="v30"></a>
## Version 3.0: Swarm Governance and Production Evidence Edition

**Released:** April 2026  
**Core concept:** The Governance OS for Autonomous AI.

Version 3.0 shifted AI SAFE² from framework coverage toward engineering certainty. It introduced the Cross-Pillar Governance Layer, CP.1 through CP.10, and expanded the framework to 161 controls.

Key v3.0 additions included:

- ACT Capability Tiers 1 through 4;
- the Agentic Control Plane;
- Agent Replication Governance;
- the HEAR Doctrine and named kill-switch authority;
- catastrophic-risk thresholds;
- AI incident feedback integration;
- active-defense and deception controls;
- AIVSS amplification-aware risk scoring;
- production-oriented controls for memory, RAG, runtime drift, swarm containment, and cloud AI platforms.

**Control count:** 151 pillar controls plus 10 cross-pillar governance controls = **161 total controls**.

v3.1 does not replace those capabilities. It hardens the protocol and enforcement semantics layered on top of them.

---

<a id="v21"></a>
## Version 2.1: Advanced Agentic and Distributed AI Edition

**Released:** November 2025

Version 2.1 expanded the framework to 128 controls and introduced deeper non-human identity, swarm, memory, and distributed-agent governance.

---

<a id="v20"></a>
## Version 2.0: Enterprise Operations Edition

**Released:** October 2025

Version 2.0 expanded AI SAFE² to 99 controls with enterprise governance and NIST/ISO mapping.

---

<a id="v10"></a>
## Version 1.0: Foundational Concepts

**Released:** June 2025

Version 1.0 established the original ten-topic foundation that later evolved into the five-pillar model.
