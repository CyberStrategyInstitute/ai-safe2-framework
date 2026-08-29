# AI SAFE² v3.1.0

**Status:** Release candidate / draft PR

AI SAFE² v3.1.0 realigns the MCP security profile to Model Context Protocol `2026-07-28`, removes protocol-owned session state as a governance dependency, expands CP.5.MCP from 13 to 19 sub-controls, and makes the framework/reference-implementation boundary explicit.

## Governing architecture

AI SAFE² specifies what must be governed and enforced. It does not mandate one implementation mechanism.

Cyber Strategy Institute publishes NEXUS as the reference implementation for the east-west agent-to-agent and agent-to-tool enforcement planes. Organizations may use NEXUS or another implementation when they can demonstrably satisfy the applicable AI SAFE² control outcomes and produce independently reconstructable evidence.

### Enforcement planes

| Plane | Traffic | Reference enforcement point | Authorizes |
|---|---|---|---|
| North-south | Agent to model provider | `gateway/` | Content and spend |
| East-west | Agent to agent | NEXUS A2A gateway | Delegation and identity |
| Agent-to-tool | Agent to MCP server | NEXUS MCP adapter | Tool reachability and returned-content trust |

The enforcement points remain separate while sharing one policy vocabulary, one principal definition, and one audit record schema.

## CP.5 profile authorship rule

> A CP.5 profile MUST NOT bind a control to a construct owned by the protocol it profiles.

MCP `2026-07-28` retires the `initialize`/`initialized` handshake and `Mcp-Session-Id` as required lifecycle constructs. AI SAFE² v3.1 therefore binds governance to framework-owned constructs: verified principal, declared capability grant, provenance baseline, recorded delegation chain, and explicit trust-establishment events.

## MCP profile changes

The CP.5.MCP profile expands from 13 to 19 sub-controls while the overall AI SAFE² framework remains at 161 controls.

New v3.1 MCP attack/control coverage includes:

- MCP-14, Extension Capability Negotiation Governance
- MCP-15, Header and Body Assertion Integrity
- MCP-16, State Handle Binding and Lifecycle
- MCP-17, MRTR Round-Trip Integrity
- MCP-18, Catalog Cache Integrity
- MCP-19, Authorization Chain Integrity

The profile explicitly covers authorization desynchronization, stale or poisoned catalog caches, replay across governance windows, OAuth resource/audience mix-up, localhost impersonation, and protocol capability drift.

## Compatibility

AI SAFE² v3.1 is intended as a point release. Existing NEXUS persistence aliases `session`, `cross-session`, and `permanent` remain accepted during a twelve-month compatibility window while canonical terminology migrates to protocol-independent governance scopes.

The existing `skills/mcp/data/ai-safe2-controls-v3.0.json` remains available for rollback. The v3.1 control dataset is additive.

## Challenge Lab alignment

Challenge 001 remains a falsification-first experiment. AI SAFE² is the framework under test, and NEXUS is a reference implementation under test. Neither receives credit by definition.

For confirmatory runs, manifests must pin the framework version, applicable control-profile version, protocol version, reference-implementation commit, adapter version/commit/hash, policy bundle hash, and grader hash.

Challenge results must distinguish experimental claim maturity from framework/profile conformance. A successful outcome from a nonconformant reference implementation does not establish control conformance.

Validation is scoped to the enforcement planes actually exercised by preregistered scenarios. Successful A2A governance does not establish MCP/tool-plane or model-provider-plane validation unless those planes are independently included and graded.

## Release gates

The v3.1.0 tag MUST NOT be created until all of the following are satisfied:

- `ALL_RULES` resolves to 52 scanner rules.
- Existing gateway and MCP toolkit test suites are green.
- No scanner rule requires optional `server/discover` behavior.
- No inbound links remain to the misspelled `cp5_mcp_sever_security.md` path.
- `mcp_spec_version` is present on all MCP-facing controls.
- Legacy NEXUS persistence aliases continue to resolve.
- The MCP-19 authorization decision is implemented and documented.
- MCP-19 scanner findings are scoped to the agent-to-tool plane or remain advisory-only until tuned.
- Pull-request licensing language is reconciled with the root MIT + CC-BY-SA licensing model while retaining NEXUS Apache 2.0 where intentional.
- Red-team fixtures cover handle guessing, header/body authorization desync, MRTR replay, cache staleness, OAuth mix-up, and localhost impersonation.
- Challenge 001 preregistration is re-frozen if normative framework, profile, reference implementation, policy, or grader behavior changes.

## Known release-blocking decisions

### MCP-19 authorization

The current AI SAFE² MCP server uses opaque static bearer tokens. Those tokens do not carry an OAuth audience and therefore cannot satisfy MCP-19 audience validation as written. The preferred migration is a JWT wrapper with an `aud` claim while preserving the existing entitlement flow. Existing consumers should receive the same twelve-month compatibility treatment applied elsewhere in this point release.

### NEXUS MCP adapter

The v3.1 adapter contract is intentionally fail-closed. Unimplemented methods must continue to raise rather than silently return success. The preferred implementation path is promotion and hardening of the existing MCP security toolkit proxy components instead of an independent rewrite.

## Source package provenance

Release working package: `ai-safe2-v3.1-mcp-2026-07-28.zip`

SHA-256: `751cc5880151937cd042addd3e2d9bc8dca15b2f96ca5f709c2faa4b67b70a39`

Local package validation performed before staging this release candidate:

- JSON parse: PASS
- Python compile for packaged `.py` files: PASS

These checks validate package syntax only. They do not replace repository CI, integration tests, red-team fixtures, or independent Challenge Lab evidence.
