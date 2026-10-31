# NEXUS MCP Adapter

**Plane:** agent-to-tool
**Protocol:** Model Context Protocol
**Spec versions:** `2026-07-28` primary, `2025-11-25` legacy for 12 months
**Profile:** [CP.5.MCP](../../../00-cross-pillar/cp5_mcp_server_security.md)
**Status:** specification complete; implementation scaffolding only

## Positioning

AI SAFE² specifies what must be governed and enforced. NEXUS provides CSI's reference implementation for enforcing those requirements across agent-to-agent and agent-to-tool interactions. Organizations may use NEXUS or another implementation that demonstrably satisfies the applicable AI SAFE² controls.

## Purpose

NEXUS originally covered the east-west agent-to-agent plane. MCP is the agent-to-tool plane. The v3.1 adapter establishes a named first-party enforcement contract for that plane without making NEXUS a mandatory conformance mechanism.

The adapter contract covers return-path sanitization, attributable audit, principal-scoped economic ceilings, delegation lineage, extension grants, header/body assertion integrity, state-handle binding, MRTR integrity, catalog cache integrity, and authorization-chain validation.

Some controls remain outside an in-path adapter. MCP-1 command-construction safety is a server/build-time concern. MCP-4 local binary integrity must be established before process execution. Client-internal caching remains a client conformance responsibility when it does not traverse the adapter.

## Enforcement contract

Inbound, before dispatch:

1. Resolve the principal from a verified credential.
2. Compare `Mcp-Method` and `Mcp-Name` with the JSON-RPC body and reject disagreement.
3. Verify the capability grant covers the requested tool and extensions.
4. Validate any state handle against the verified principal.
5. Validate MRTR responses and replay protections.
6. Enforce the principal's economic ceiling.
7. Emit attributable evidence.

Outbound, before content reaches model context:

1. Sanitize tool-return content.
2. Clamp cache TTL and compare catalog provenance on revalidation.
3. Bind newly minted state handles to the principal.
4. Record result metadata and redact credential-like handles from traces.

## Legacy binding

For MCP `2025-11-25`, `Mcp-Session-Id` is mapped to a principal-scoped state handle. It is not treated as identity or as the authorization boundary. The compatibility binding can be removed after the twelve-month migration window without changing the normative control outcomes.

## Implementation status

`adapter.py` is an interface skeleton. It is not a deployable security control. Every enforcement method raises `NotImplementedError` until an implementation is connected and tested. This is intentional fail-closed behavior.

### What is implemented: tool-call authorization

`authorize_tool_call` (enforcement step 3, capability and authorization) is
implemented and tested as a pure decision function in `authz.py`, with
`MCPAdapter.authorize_tool_call` wiring it to a verified `Principal`. It is a
Python mirror of `opa/nexus-authz.rego`, ported back from Agency Check's
TypeScript edge adapter (`src/nexus/authz.ts`, `src/nexus/context.ts`) and
re-aligned to the current upstream policy. Tests are in
`sdk/python/tests/test_mcp_adapter_authz.py`; when an `opa` binary is available
(`OPA_BIN`) the same input table is evaluated by OPA and by the port and the
decisions must agree. Without OPA those parity tests skip and parity is
**not assessed**.

The `_meta` NEXUS context (`nexusCaelEnvelopeHash`, delegation depth, requested
capabilities, and similar) is caller-asserted. It can only narrow a decision: the
delegation depth used is the larger of the verified chain and the declared depth,
the context compartment is never taken from `_meta` (the deployment supplies `context_compartment`, default `TASK_CONTEXT`, and a differing `nexusContextCompartment` is rejected; `authz.ts` passed the `_meta` value straight through, which let a caller select `CREDENTIAL_SURFACE`), and `nexusSenderDID` is never treated as identity: a caller-asserted DID is not a verified credential.

### What was not ported, and why

| Item in the Agency Check adapter | Status here | Reason |
| --- | --- | --- |
| Principal identity from OAuth props (`did`) and scope-to-capability mapping (`toolsForScopes`) in `pipeline.ts` | Not ported | Tied to Agency Check's OAuth provider. `establish_trust` stays `NotImplementedError`; the adapter takes a `Principal` the caller has already verified. A bearer token alone does not satisfy MCP-19. |
| Revocation snapshot from a per-user Durable Object (`stub.revokedAgents()`) | Not ported | Storage is deployment-specific. The adapter takes `policy_data` and returns HALT when no revocation snapshot is supplied; missing data is never "not revoked". |
| Mandate and approval data | Not ported | Agency Check passes an empty mandate set and no approvals, so there is nothing to port. Here they arrive through `policy_data` and are not fetched. Unlike the Rego (any truthy `mandates.active[id]` satisfies every gated tool for every caller), a mandate here must carry `agent_id` equal to the principal, `tools` containing the tool, and a future numeric `expires_at_ns` (AUTHZ-DIV-4). Agency Check's `authz.ts` has no mandate binding to compare because its mandate set is always empty. |
| NOR receipt creation and signing (`makeNor`) | Not ported | Signing keys and the receipt store belong to the deployment. The adapter returns the decision document as `AdapterResult.evidence`; emitting a signed receipt is enforcement step 7 and remains unimplemented. |
| First-failing-condition `deny_reason` in `authz.ts` | Superseded | The older Rego published an empty `deny_reason`, which `authz.ts` worked around. The current `opa/nexus-authz.rego` joins and sorts its reasons, and the port matches it. `allow` is identical in all versions. |
| Cloudflare Workers runtime, `crypto.subtle`, request routing | Not applicable | Runtime-specific; this is a Python reference. |

Four divergences from the Rego are deliberate and fail closed (AUTHZ-DIV-1 to
AUTHZ-DIV-4, documented in `authz.py` and pinned by tests): non-integer
delegation depth, a `config_change` with no `change_hash`, and absent parent
capabilities each deny, where the Rego would allow because an undefined
comparison removes the deny condition; and a mandate not bound to the
principal, tool and expiry does not satisfy a mandate-gated tool, where the
Rego accepts any active mandate ID. They should be fixed in the policy, at
which point the pinning tests flip.

This enforces one step. All other enforcement methods are unchanged and still raise
`NotImplementedError`. The adapter as a whole remains not production-ready.

Production users should deploy an implemented NEXUS adapter or another implementation that demonstrably satisfies the CP.5.MCP outcomes and evidence requirements.
