# AI SAFE² Integrations
### One governance model across design-time, CI, runtime, agent-to-agent, and agent-to-tool surfaces

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](README.md)
[![Surface](https://img.shields.io/badge/Surface-Integrations-820F1A?style=flat-square)](INTEGRATIONS.md)
[![Model](https://img.shields.io/badge/Model-3_Enforcement_Planes-808080?style=flat-square)](00-cross-pillar/README.md)

[Framework Home](README.md) | [Cross-Pillar Governance](00-cross-pillar/README.md) | [AISM](AISM/) | [NEXUS](NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

## Integration Goal

AI SAFE² should fit around the tools an organization already uses. The framework defines the governance outcomes and evidence. Repository components provide reference paths for enforcing those requirements at different points in the lifecycle.

The current v3.1 architecture separates five operational surfaces:

| Surface | Repository component | Role |
|---|---|---|
| **Design-time** | `skills/`, MCP server | Framework guidance, control lookup, classification, code-review support |
| **Pre-commit / CI** | `scanner/` | Static-analysis and governance-gap detection |
| **North-south runtime** | Gateway v3.0 | Model/provider boundary enforcement and audit |
| **East-west runtime** | NEXUS v0.3 | Agent identity, delegation, lineage, policy, revocation, receipts |
| **Agent-to-tool runtime** | CP.5.MCP + NEXUS MCP adapter/toolkit | MCP/tool authorization, provenance, returned-content trust, state and resource binding |

Component versions are independent from the framework version. AI SAFE² is currently v3.1; the Gateway remains v3.0 and NEXUS remains v0.3 until those components have their own tested releases.

---

## v3.1 Architecture

```text
                          AI SAFE2 v3.1
                    governance + evidence model
                              |
          +-------------------+-------------------+
          |                   |                   |
     Design / Build        Pre-Commit          Runtime
          |                   |                   |
      skills/ +            scanner/       +-------+--------+
      MCP server                           |       |        |
                                       north   east-west  agent-tool
                                       south      |        |
                                         |       NEXUS    CP.5.MCP
                                      Gateway             + adapter
```

### North-south

Agent/model-provider interactions are governed for content boundaries, policy, economic ceilings, response inspection, and human authorization. The current reference component is [Gateway v3.0](gateway/README.md).

### East-west

Agent-to-agent interactions require identity, delegated authority, lineage, revocation, and evidence. [NEXUS v0.3](NEXUS/) is CSI's first-party reference implementation.

### Agent-to-tool

MCP/tool interactions use the [CP.5.MCP v3.1 profile](00-cross-pillar/cp5_mcp_server_security.md). The profile contains MCP-1 through MCP-19 and is aligned to MCP `2026-07-28`.

The new NEXUS MCP adapter is an enforcement contract/scaffold and must not be described as production-ready until its required methods are implemented and tested.

---

## Core Data Model

```text
skills/mcp/data/ai-safe2-controls-v3.0.json  stable 161-control core taxonomy
skills/mcp/data/mcp-profile-v3.1.json       CP.5.MCP v3.1 profile overlay
```

The v3.0 filename on the core taxonomy is historical provenance. AI SAFE² v3.1 did not add new core controls.

Current counts:

- **161 core framework controls**;
- **CP.1 through CP.10 core Cross-Pillar Governance controls**;
- **MCP-1 through MCP-19 profile controls**;
- **CP.11 UAS as a compliance overlay**, not 27 new independent core controls.

---

## Skills and MCP Server

The Skills ecosystem provides model-facing AI SAFE² guidance. The MCP server adds live control/profile lookup and governance workflows.

Current entry points:

- [Skills overview](skills/README.md)
- [Canonical skill](skills/SKILL.md)
- [MCP server](skills/mcp/README.md)

The MCP server can query the 161-control core taxonomy and the separate 19-control MCP profile overlay without double-counting profile controls as core controls.

---

## Scanner

The [AI SAFE² Scanner](scanner/README.md) provides pre-commit/CI analysis.

AI SAFE² v3.1 adds 12 grouped MCP static-analysis rules to the existing scanner, bringing the expected rule registry to **52 rules**.

Important boundaries:

- no `server/discover` presence requirement;
- MCP-19 intended-resource/audience/SSRF findings are advisory until deployment behavior can be proven;
- static analysis contributes evidence but does not establish full runtime conformance.

---

## Gateway

The [Gateway](gateway/README.md) remains **component version 3.0** and is the repository's north-south runtime reference path.

Do not rewrite Gateway v3.0 audit records as v3.1 merely because the framework advanced. Component-version provenance is part of the evidence chain.

---

## NEXUS

[NEXUS v0.3](NEXUS/) is CSI's first-party reference implementation for governed agent-to-agent interactions and the reference path for the v3.1 agent-to-tool contract.

AI SAFE² conformance does not require NEXUS specifically. Another implementation may conform when it satisfies the applicable controls and produces equivalent reconstructable evidence.

### v3.1 persistence semantics

Governance-bearing persistence uses:

- `request`;
- `handle_scoped`;
- `durable`.

Older NEXUS `SESSION`, `CROSS_SESSION`, and `PERMANENT` values remain compatibility aliases during migration. Protocol correlation fields such as AOS `sessionId` may still exist without becoming identity or authorization boundaries.

---

## MCP `2026-07-28`

AI SAFE² v3.1 updates the MCP security model for the current profile binding.

Key additions include:

- extension capability negotiation;
- header/body assertion integrity;
- principal-bound state handles;
- MRTR request/response integrity and replay resistance;
- catalog-cache provenance revalidation;
- intended-resource/audience validation and SSRF boundaries.

MCP `2025-11-25` remains a legacy compatibility binding during the migration window.

---

## Integration Decision Guide

| Need | Start here |
|---|---|
| Teach an AI coding assistant the framework | [skills/SKILL.md](skills/SKILL.md) |
| Query controls/profile data live | [skills/mcp/README.md](skills/mcp/README.md) |
| Catch code/config governance gaps in CI | [scanner/README.md](scanner/README.md) |
| Enforce the model/provider boundary | [gateway/README.md](gateway/README.md) |
| Govern agent-to-agent authority | [NEXUS/README.md](NEXUS/README.md) |
| Govern MCP/tool use | [CP.5.MCP](00-cross-pillar/cp5_mcp_server_security.md) |
| Explore controls visually | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/) |
| Test claims adversarially | [Challenge Lab](challenges/README.md) |

---

## Conformance Rule

Installing an AI SAFE² repository component is not itself evidence of conformance.

For any integration, record:

- framework and profile version;
- component/implementation version;
- applicable control IDs;
- enforcement plane;
- principal and authority context;
- policy and configuration version;
- evidence produced;
- unresolved assumptions or unsupported claims.

---

## Navigation

[Framework Home](README.md) | [Cross-Pillar Governance](00-cross-pillar/README.md) | [AISM](AISM/) | [NEXUS](NEXUS/) | [Skills](skills/README.md) | [Scanner](scanner/README.md) | [Gateway](gateway/README.md) | [Dashboard](dashboard/README.md)

---

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
