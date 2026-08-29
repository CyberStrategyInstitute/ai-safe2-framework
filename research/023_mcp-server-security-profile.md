# Research Note 023: MCP Server Security Profile
### Research foundation for CP.5.MCP

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Research](https://img.shields.io/badge/Research-023-820F1A?style=flat-square)](./023_mcp-server-security-profile.md)
[![MCP](https://img.shields.io/badge/MCP-2026--07--28-808080?style=flat-square)](../00-cross-pillar/cp5_mcp_server_security.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Research 024](./024_mcp_consumer_protection.md)

**Current revision:** August 2026  
**Historical origin:** April 2026 research that originally supported the v3.0 MCP profile  
**Current profile:** CP.5.MCP v3.1, MCP-1 through MCP-19

---

## Purpose

This note explains why Model Context Protocol deployments require a dedicated AI SAFE² CP.5 profile and how the security model changed for MCP `2026-07-28`.

The original April 2026 research focused on structural MCP risks such as unsafe command construction, tool-response injection, provenance gaps, local process execution, tool squatting, and consumer trust. Those findings remain relevant, but v3.1 changes the governance model in an important way: **the security boundary must not depend on protocol-owned session constructs.**

The current profile therefore binds governance to verified principals, capability grants, delegation chains, provenance baselines, policy context, trust-establishment events, and explicit state handles.

---

## Architectural Distinctions

### Local process execution

MCP may run tools through local process boundaries such as stdio. In those deployments, ordinary network controls do not provide the complete security boundary. The implementation must verify what binary or server is being executed and prevent untrusted data from becoming executable command construction.

This supports MCP-1 and MCP-4.

### Tool return paths are untrusted input

Tool responses enter the agent's reasoning context and can therefore become an indirect prompt-injection surface. Returned content must be treated as untrusted even when the tool call itself was authorized.

This supports MCP-2 and the broader P1 indirect-input controls.

### Catalogs and schemas are authority-bearing data

Tool descriptions, resource catalogs, prompt catalogs, and schemas influence what an agent believes it can call and how it should call it. Changes to those catalogs can therefore change effective authority without changing application code.

This supports MCP-11 and MCP-18.

### Authorization is independent of a transport session

MCP `2026-07-28` does not justify treating a protocol session identifier as identity or authorization. Protected tool use must bind to a verified principal and intended resource or audience.

This supports MCP-7, MCP-12, MCP-13, MCP-16, and MCP-19.

---

## v3.1 MCP Control Model

| Range | Security concern |
|---|---|
| **MCP-1 through MCP-6** | Command safety, returned-content trust, least privilege, server integrity, audit, input validation |
| **MCP-7 through MCP-13** | Trust establishment, economic ceilings, secret boundaries, delegation, provenance, state, revocation |
| **MCP-14 through MCP-19** | Extension negotiation, assertion integrity, state handles, MRTR integrity, cache integrity, authorization-chain integrity |

The normative definitions are maintained in [CP.5.MCP](../00-cross-pillar/cp5_mcp_server_security.md). This research note intentionally does not duplicate the complete normative matrix.

---

## v3.1 Protocol-Independence Rule

> A CP.5 profile MUST NOT bind a control to a construct owned by the protocol it profiles.

For MCP, that means:

- identity is the verified principal, not `Mcp-Session-Id`;
- authorization is the capability/resource decision, not possession of a state handle;
- continuity is expressed through governed state, not protocol session lifetime;
- revocation invalidates authority independently of transport lifecycle;
- evidence must identify the principal, grant, policy, provenance, and relevant state handle explicitly.

MCP `2025-11-25` remains a legacy compatibility binding during migration. Legacy session identifiers may be recorded as principal-scoped state handles, but they are not the governance identity.

---

## Threat and Control Rationale

| Threat / failure mode | v3.1 response |
|---|---|
| Dynamic command execution from untrusted arguments | MCP-1 command-construction safety |
| Malicious tool output influencing the model | MCP-2 return-path sanitization |
| Excessive tool/resource exposure | MCP-3 least privilege |
| Tampered local binary or remote endpoint | MCP-4 integrity and identity verification |
| Unreconstructable tool activity | MCP-5 attributable audit evidence |
| Malformed or policy-incompatible inputs | MCP-6 schema/policy validation |
| Tool use before verified trust context | MCP-7 trust establishment |
| Runaway cost/consumption | MCP-8 economic ceiling |
| Secret leakage through context, arguments, or logs | MCP-9 secret boundary |
| Lost multi-agent delegation lineage | MCP-10 delegation evidence |
| Catalog/tool substitution | MCP-11 provenance baseline |
| Persistent state detached from principal/policy | MCP-12 state binding |
| Stale authority after revocation | MCP-13 reauthorization |
| Unapproved extension behavior | MCP-14 capability negotiation |
| Header/body method disagreement | MCP-15 assertion integrity |
| State-handle possession treated as identity | MCP-16 lifecycle/binding |
| Replayed or mismatched model-mediated tool result | MCP-17 round-trip integrity |
| Stale cache hiding catalog/schema drift | MCP-18 cache integrity |
| Wrong-resource token, redirect abuse, metadata confusion, SSRF | MCP-19 authorization-chain integrity |

---

## ACT Tier Implications

MCP risk scales with autonomy and consequence, not merely with whether MCP is present.

- **ACT-1:** Human review reduces immediate action risk, but server integrity, secret handling, and returned-content trust still matter.
- **ACT-2:** Tool actions occur between human checkpoints, increasing the importance of explicit input/output enforcement and auditability.
- **ACT-3:** Autonomous action requires stronger authorization, state, revocation, economic, and evidence controls.
- **ACT-4:** Orchestration adds delegation, descendant authority, replication, and cascade risk. MCP tool use must preserve lineage and remain bounded by CP.4, CP.8, CP.9, and CP.10 requirements.

---

## Evidence Implications

A strong MCP evidence bundle should identify, where applicable:

- `framework_version`;
- `control_profile_version`;
- `mcp_spec_version`;
- verified principal;
- capability grant;
- delegation chain;
- provenance baseline;
- trust-establishment event;
- transport and server identity;
- state handle;
- catalog/schema hashes and cache revalidation;
- intended-resource/audience result;
- policy/adapter version or hash.

This is the evidence needed to reconstruct why a protected tool action was permitted or rejected.

---

## Relationship to NEXUS and the Toolkit

AI SAFE² defines the required outcomes and evidence. NEXUS is CSI's first-party reference implementation for the applicable agent-to-tool enforcement path. Alternative implementations may conform if they produce equivalent control outcomes and evidence.

The MCP security toolkit provides assessment and protective utilities, including `mcp-score`, `mcp-scan`, and `mcp-safe-wrap`. Those tools help operationalize the profile but do not by themselves prove conformance.

---

## Research Continuity

The April 2026 findings remain part of the historical basis for the profile. v3.1 does not erase that research; it generalizes the profile so the governance contract survives protocol evolution.

Research Note 024 addresses the complementary consumer-side protection problem.

---

## 🔗 Navigation

[Framework Home](../README.md) | [CP.5.MCP](../00-cross-pillar/cp5_mcp_server_security.md) | [Research 024](./024_mcp_consumer_protection.md) | [NEXUS](../NEXUS/) | [MCP Toolkit](../examples/mcp-security-toolkit/)

---

*AI SAFE² v3.1 Research Foundation · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
