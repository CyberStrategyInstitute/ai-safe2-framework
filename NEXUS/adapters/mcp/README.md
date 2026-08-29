# NEXUS MCP Adapter

**Plane:** agent-to-tool
**Protocol:** Model Context Protocol
**Spec versions:** `2026-07-28` (primary), `2025-11-25` (legacy, 12 months)
**Profile:** [CP.5.MCP](../../../00-cross-pillar/cp5_mcp_server_security.md)
**Status:** specification complete, implementation scaffolding only

---

## AI SAFE² and NEXUS positioning

AI SAFE² specifies what must be governed and enforced. NEXUS provides CSI's reference implementation for enforcing those requirements across agent-to-agent and agent-to-tool interactions. Organizations may use NEXUS or another implementation that demonstrably satisfies the applicable AI SAFE² controls.


## Why this exists

NEXUS was scoped east-west: agent to agent. MCP traffic is agent-to-tool. It is neither model egress nor agent-to-agent, and until v3.1 it had no named enforcement point in the framework. `examples/mcp-security-toolkit/.../wrap/proxy.py` had been functioning as one informally.

This adapter promotes that role into NEXUS. The result is the property the framework has been describing as its objective: install one thing, get governed tool traffic, the way HTTPS gave the web a trustworthy channel without anyone re-implementing TLS per site.

## What it does and does not cover

The TLS analogy is precise, including its limits. TLS made the channel trustworthy. It did not make content trustworthy, which is why a fully HTTPS web still has an OWASP Top 10.

| Covered by this adapter | Enforcement |
|---|---|
| MCP-2 Output sanitization on the return path | In-path inspection before content reaches model context |
| MCP-5 Tool invocation audit | NOR record per call, bound to principal |
| MCP-8 Economic ceiling | Per-principal accounting, fail-closed halt |
| MCP-10 Delegation edge monitoring | Existing NEXUS lineage, extended to tool edges |
| MCP-14 Extension capability negotiation | Grant recorded at trust establishment |
| MCP-15 Header/body assertion integrity | Reject on mismatch before dispatch |
| MCP-16 State handle binding | Handle mint and validation, `<principal>:<handle>` |
| MCP-17 MRTR round-trip integrity | Answer binding, single-use enforcement |
| MCP-18 Catalog cache integrity | TTL clamp, revalidation diff |
| MCP-19 Authorization chain | `iss` and audience validation, CIMD, SSRF guards |

| Not covered, and why | Where it lands |
|---|---|
| **MCP-1** No dynamic command construction | A defect inside the server process. No in-path component can see it. | Scanner, build time |
| **MCP-4** stdio binary integrity | Verification must precede process spawn, before any proxy exists | Adapter at spawn, or pre-launch manifest check |
| **Client-internal caching** | If a client caches without traversing the adapter, nothing in path observes it | Client conformance requirement |

That residue is small and honest. Do not claim otherwise in marketing material; the credibility cost of overclaiming here is higher than the value of the claim.

## Second-order effects, stated plainly

Putting NEXUS in path for all tool traffic changes NEXUS's own risk profile:

1. **Availability becomes load-bearing.** The adapter is a single point of failure for agent productivity. Fail-closed is correct for MCP-8 and it means an adapter outage stops work. This needs an explicit availability target and a documented break-glass procedure with its own audit trail.
2. **It becomes a high-value target.** The adapter holds verified identity and audit records for every agent-to-tool interaction in the estate. TLS terminators carry exactly this profile. It requires the hardening posture of a secrets-bearing component, not of a proxy.
3. **Latency lands on the hot path.** Return-path sanitization is inspection of content on the critical path. Budget it, measure it, and publish the number, because a slow adapter will be bypassed by the people it protects.

These are the right trades. They are not free, and pretending otherwise invites the first outage to become an argument against the architecture.

## Conformance

Controls state outcome and evidence. They do not name mechanisms. This adapter is the **reference implementation** of the CP.5.MCP requirements, and conformance does not require it. That statement appears once, in `00-cross-pillar/README.md`, and is deliberately not repeated per control.

## Interface contract

The adapter implements two directions.

**Inbound (agent to server), before dispatch:**

1. Resolve principal from verified credential. Reject if unresolvable and tier is ACT-2 or above.
2. Verify `Mcp-Method` and `Mcp-Name` against the JSON-RPC body. Reject on mismatch (MCP-15).
3. Check capability grant covers the requested tool and any negotiated extension (MCP-14).
4. Validate any presented state handle against `<principal>:<handle>` (MCP-16).
5. Validate `inputResponses` binding and single-use if present (MCP-17).
6. Check economic ceiling. Halt fail-closed on breach (MCP-8).
7. Record to NOR.

**Outbound (server to agent), before content reaches model context:**

1. Sanitize return-path content (MCP-2).
2. Clamp `ttlMs`, diff catalog against provenance baseline on revalidation (MCP-18, MCP-11).
3. Bind and register any newly minted state handle (MCP-16).
4. Record result metadata to NOR. Redact handles from traces.

## Legacy adapter

`transport_binding = mcp/2025-11-25` maps `Mcp-Session-Id` to a principal-scoped handle so a single control set covers both spec versions. At the close of the twelve-month window, delete the legacy adapter. No control text changes, because no control references session directly. That is the payoff of the CP.5 authorship rule.

## Implementation status

`adapter.py` in this directory is an **interface skeleton with unimplemented bodies**. It has not been executed, integrated with the NEXUS SDK, or tested. It defines the contract above so implementation can proceed against a fixed shape. Every enforcement point is marked `NotImplementedError` deliberately rather than stubbed to return success, so an incomplete adapter fails closed rather than silently passing traffic.

Do not deploy it. Implement against it.
