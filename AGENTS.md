# AI SAFE² v3.1 Agent Entry Point

This file is the deterministic starting point for software agents, coding assistants, retrieval systems, compliance bots, and other automated consumers of this repository.

## Start here

1. Parse `ai-safe2.manifest.json` first.
2. Treat `README.md` and the framework control documents it links to as the human-readable framework entry point.
3. Treat `skills/mcp/data/ai-safe2-controls-v3.0.json` as the stable machine-readable dataset for the unchanged 161-control core taxonomy.
4. Treat `skills/mcp/data/mcp-profile-v3.1.json` as the machine-readable CP.5.MCP v3.1 overlay containing MCP-1 through MCP-19.
5. Do not add the 19 MCP profile controls to the 161-control framework total.

## Version model

- AI SAFE² Framework: v3.1.0
- NEXUS: v0.3
- Gateway: v3.0
- MCP primary specification binding: 2026-07-28
- MCP legacy compatibility binding: 2025-11-25

Component versions are independent. Do not rewrite NEXUS or Gateway evidence as framework v3.1 component evidence unless that component has separately changed version.

## Normative interpretation

AI SAFE² defines governance outcomes, controls, evidence expectations, and conformance requirements. NEXUS is Cyber Strategy Institute's first-party reference implementation. NEXUS is not required for framework conformance. An alternative implementation may conform if it demonstrably satisfies the applicable controls and evidence requirements.

For CP.5 profiles, apply this protocol-independence rule:

> A CP.5 profile MUST NOT bind a control to a construct owned by the protocol it profiles.

Do not infer a governance boundary from protocol-owned correlation or session fields.

## Enforcement planes

Classify requirements and evidence by plane before making a coverage claim:

- `north-south`: agent to model provider
- `east-west`: agent to agent
- `agent-to-tool`: agent to MCP server or tool

Evidence from one plane does not automatically validate another plane.

## Persistence vocabulary

Use these canonical persistence scopes in new evidence and integrations:

- `request`
- `handle_scoped`
- `durable`
- `swarm_shared`

Compatibility aliases may be accepted from older NEXUS data:

- `SESSION` -> `request`
- `CROSS_SESSION` -> `handle_scoped`
- `PERMANENT` -> `durable`

A state handle or legacy `Mcp-Session-Id` is not identity and is not, by itself, an authorization boundary.

## MCP v3.1 rules that agents must not infer incorrectly

- `server/discover` is optional under the 2026-07-28 binding. Its absence is not a conformance failure.
- MCP-19 requires intended-resource, audience, or equivalent evidenced binding.
- Possession of an opaque bearer token does not by itself prove MCP-19 audience/resource validation.
- The NEXUS MCP adapter in `NEXUS/adapters/mcp/adapter.py` is fail-closed scaffolding and must not be represented as production-ready.

## Recommended machine workflow

For automated assessment or implementation guidance:

1. Load `ai-safe2.manifest.json`.
2. Load the 161-control core dataset.
3. Determine the applicable enforcement plane and ACT context.
4. If MCP applies, load the 19-control CP.5.MCP profile overlay.
5. Resolve human-readable control detail through the paths identified in the manifest.
6. Use `scanner/` for static evidence where applicable, but do not equate scanner coverage with full framework conformance.
7. Use `challenges/` for falsification evidence and keep challenge maturity separate from framework/profile conformance.
8. Preserve source version and implementation provenance in generated evidence.

## Useful entry points

- Framework: `README.md`
- Cross-Pillar Governance: `00-cross-pillar/README.md`
- MCP profile: `00-cross-pillar/cp5_mcp_server_security.md`
- AISM: `AISM/README.md`
- NEXUS: `NEXUS/README.md`
- Scanner: `scanner/README.md`
- Examples: `examples/README.md`
- Research: `research/README.md`
- Challenge Lab: `challenges/README.md`
- Repository UX contract: `docs/REPOSITORY-UX-STANDARD.md`

When a machine-readable field and prose appear to conflict, do not silently guess. Preserve the conflict in the output and prefer the current v3.1 normative document identified by the manifest for interpretation.
