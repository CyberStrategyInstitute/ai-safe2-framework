# CP.5.MCP — MCP Server Security Profile

**AI SAFE² version:** 3.1
**MCP specification:** `2026-07-28` primary; `2025-11-25` legacy compatibility
**Control family:** CP.5 Server and Tool Security
**Profile controls:** MCP-1 through MCP-19

## Normative scope

This profile governs the agent-to-tool enforcement plane for Model Context Protocol deployments. AI SAFE² controls define required outcomes and evidence. NEXUS is CSI's reference implementation; organizations may use NEXUS or another implementation that demonstrably satisfies the applicable controls.

### Protocol-independence rule

A CP.5 profile MUST NOT bind a control to a construct owned by the protocol it profiles. Governance therefore binds to verified principals, capability grants, provenance baselines, delegation chains, state handles, and explicit trust-establishment events rather than transport sessions or vendor lifecycle constructs.

MCP `2026-07-28` removes the required `initialize`/`initialized` handshake and `Mcp-Session-Id`. Optional protocol features such as `server/discover` MUST NOT become mandatory AI SAFE² presence requirements.

## Controls

| ID | Control | Required outcome |
|---|---|---|
| MCP-1 | Command Construction Safety | Tool servers do not construct executable commands from untrusted arguments without strict allowlisting and escaping. |
| MCP-2 | Return-Path Content Sanitization | Tool output is treated as untrusted content and inspected before entering model context. |
| MCP-3 | Least-Privilege Tool Exposure | A principal can reach only explicitly granted tools and resources. |
| MCP-4 | Server/Binary Integrity | Local and stdio MCP servers are verified before execution; endpoint identity is verified for remote transports. |
| MCP-5 | Tool Invocation Audit | Every protected invocation emits attributable, reconstructable evidence. |
| MCP-6 | Input Validation | Tool inputs are validated against the authorized schema and policy before dispatch. |
| MCP-7 | Trust Establishment | A verified principal and policy context exist before protected tool use. |
| MCP-8 | Economic Ceiling | Consumption is accounted to a principal and fails closed at the authorized ceiling. |
| MCP-9 | Secret Boundary | Secrets are not exposed through arguments, logs, model context, or untrusted tool output. |
| MCP-10 | Delegation Edge Monitoring | Agent-to-tool actions retain the originating delegation lineage. |
| MCP-11 | Catalog Provenance | Tool/resource/prompt catalogs are compared to an authorized provenance baseline at trust establishment and revalidation. |
| MCP-12 | Principal-Scoped State | Durable or handle-scoped state is bound to the verified principal and policy context. |
| MCP-13 | Revocation and Reauthorization | Revocation or material policy change invalidates prior authorization without relying on a transport session boundary. |
| MCP-14 | Extension Capability Negotiation | Extensions are reachable only when included in the principal's capability grant and recorded at trust establishment. |
| MCP-15 | Header/Body Assertion Integrity | `Mcp-Method` and `Mcp-Name`, when present, agree with the JSON-RPC body; disagreement is rejected before dispatch. |
| MCP-16 | State Handle Binding and Lifecycle | State handles are unguessable, expiring, principal-bound credentials and are never accepted as identity by possession alone. |
| MCP-17 | MRTR Round-Trip Integrity | Model-mediated tool responses are bound to the originating request, validated as untrusted input, and protected against replay. |
| MCP-18 | Catalog Cache Integrity | Cache TTLs are policy-bounded; cache keys include trust context; revalidation detects catalog/schema provenance drift. |
| MCP-19 | Authorization Chain Integrity | Protected requests validate issuer, intended resource/audience, redirect/resource binding, authorization metadata, and SSRF boundaries before state change. |

## MCP-19 conformance note

Opaque static bearer tokens do not contain an audience claim. Deployments using such tokens MUST NOT claim MCP-19 audience-validation conformance unless equivalent resource binding is independently established and evidenced. The AI SAFE² reference server's legacy static-token mode is therefore compatibility-only for MCP-19. JWT/OAuth deployments must validate the intended audience/resource before dispatch.

## Evidence minimum

Evidence for this profile SHOULD identify:

- `framework_version`
- `control_profile_version`
- `mcp_spec_version`
- `principal_id`
- `capability_grant_id`
- `delegation_chain_id`
- `provenance_baseline_id`
- `trust_establishment_id`
- `mcp_transport`
- `mcp_server_identity`
- `mcp_catalog_hash` and prior hash when revalidated
- `cache_ttl` and `cache_revalidation_result`
- `oauth_resource` and `oauth_audience_validation_result` when authorization is used
- policy, adapter, and grader hashes where applicable

## Compatibility window

The `2025-11-25` transport binding remains supported for twelve months from the v3.1 release. `Mcp-Session-Id` in that binding is treated only as a principal-scoped state handle. It is not the governance identity or authorization boundary.

## Reference implementation

CSI's NEXUS MCP adapter is the first-party reference implementation path for the agent-to-tool plane. The v3.1 adapter contract is fail-closed and currently marked implementation scaffolding. Unimplemented methods raise rather than silently allowing traffic. Production deployments must use an implemented and tested enforcement component.

---

AI SAFE² v3.1, Cyber Strategy Institute
