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

Production users should deploy an implemented NEXUS adapter or another implementation that demonstrably satisfies the CP.5.MCP outcomes and evidence requirements.
