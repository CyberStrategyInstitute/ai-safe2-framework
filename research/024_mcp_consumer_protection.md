# Research Note 024: MCP Consumer Protection
### Consumer-side controls for untrusted or externally operated MCP servers

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Research](https://img.shields.io/badge/Research-024-820F1A?style=flat-square)](./024_mcp_consumer_protection.md)
[![MCP](https://img.shields.io/badge/MCP-2026--07--28-808080?style=flat-square)](../00-cross-pillar/cp5_mcp_server_security.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Research 023](./023_mcp-server-security-profile.md)

**Current revision:** August 2026  
**Historical origin:** April 2026 consumer-protection research  
**Current profile:** CP.5.MCP v3.1, MCP-1 through MCP-19

---

## Abstract

MCP consumers face a different problem from MCP server operators. A consumer may connect an agent to a server it does not control, cannot inspect continuously, and cannot assume will preserve the same tool catalog, authorization behavior, or returned-content integrity over time.

Consumer-side defenses therefore remain necessary even when the server claims to be secure.

AI SAFE² v3.1 extends the original consumer threat model to MCP `2026-07-28`, with particular emphasis on returned-content trust, catalog drift, state-handle misuse, replay, intended-resource/audience validation, and SSRF boundaries.

---

## Consumer Threat Model

### Supply-chain compromise without visible failure

A compromised server may continue returning apparently correct tool results while exfiltrating data, mutating behavior, or introducing malicious content. Functional correctness is not evidence of server integrity.

Relevant controls: MCP-2, MCP-4, MCP-5, MCP-9, MCP-11.

### Catalog or schema mutation

A previously trusted server may change tools, descriptions, schemas, or extensions. The consumer needs a provenance baseline and a revalidation policy rather than assuming that a familiar endpoint still represents the same authority surface.

Relevant controls: MCP-11, MCP-14, MCP-18.

### Cost and resource amplification

Tool loops, retries, or excessive downstream work create economic exposure for the consumer even when the remote server is not intentionally malicious.

Relevant control: MCP-8.

### Authorization confusion

A credential valid somewhere is not necessarily valid for the intended MCP resource. Consumers and gateways must avoid cross-resource token reuse and validate intended-resource/audience binding where applicable.

Relevant control: MCP-19.

### Persistent state poisoning

A malicious tool response can affect future behavior if it is written into governed memory. v3.1 describes persistence using `request`, `handle_scoped`, and `durable` scopes rather than treating a protocol session as the governance boundary.

Relevant controls: MCP-2, MCP-12, MCP-13, MCP-16, plus AI SAFE² memory-governance controls.

### Local and private-network targeting

A tool parameter, redirect, or server-driven resource request can attempt to reach loopback, link-local, metadata, private-network, or file resources that should not be reachable from an untrusted integration.

Relevant control: MCP-19.

---

## Consumer Protection Tools

### `mcp-safe-wrap`

Consumer-side wrapping can provide protections independent of the remote server's implementation, including:

- returned-content inspection before model-context entry;
- URL/target restrictions for SSRF-sensitive values;
- consumer-controlled audit evidence;
- policy checks before forwarding a protected call.

A wrapper reduces exposure but does not prove that the remote server satisfies all profile controls.

### `mcp-score`

`mcp-score` can help assess observable server posture before connection. A black-box score is a risk signal, not a complete conformance certification, because many requirements depend on internal authorization, provenance, and evidence behavior that cannot be proven externally.

### `mcp-scan`

Static scanning can detect high-value implementation patterns in code that is available for inspection. It cannot establish runtime audience binding, complete mediation, or evidence integrity on its own.

---

## v3.1 Consumer Checklist

### Before connection

- Know who operates the server and what endpoint/binary identity is expected.
- Define the minimum tools/resources the principal actually requires.
- Prefer resource- or audience-bound authorization over reusable opaque credentials.
- Establish a catalog/schema provenance baseline when the client depends on discovered tool metadata.
- Define cost/rate ceilings.
- Restrict local/private-network targets and redirects unless explicitly required.

### At trust establishment

- Verify the principal and intended server/resource.
- Record the capability grant and policy context.
- Record the tool/resource/prompt catalog hashes that influence authority.
- Negotiate only extensions the principal is authorized to use.
- Treat legacy `Mcp-Session-Id` only as a principal-scoped compatibility state handle.

### During operation

- Sanitize returned content before it enters model context or durable memory.
- Validate tool inputs against the authorized schema.
- Preserve delegation lineage for agent-originated calls.
- Detect catalog/schema changes and revalidate before protected use.
- Reject replayed or mismatched model-mediated tool responses.
- Enforce the economic ceiling.
- Produce attributable audit evidence.

### On revocation or material change

- Invalidate prior authorization without waiting for a transport session to end.
- Expire or revoke affected state handles.
- Re-establish trust when catalogs, policy, principal authority, or resource binding changes materially.

---

## Relationship to CP.5.MCP

The consumer protections map across the current 19-control profile rather than the historical 13-control baseline.

Representative mappings:

| Consumer protection | Profile controls |
|---|---|
| Returned-content scanning | MCP-2 |
| Local/server integrity checks | MCP-4 |
| Consumer-controlled audit | MCP-5 |
| Cost ceilings | MCP-8 |
| Secret redaction/brokering | MCP-9 |
| Catalog/schema pinning | MCP-11, MCP-18 |
| State-handle discipline | MCP-12, MCP-16 |
| Extension restrictions | MCP-14 |
| Replay/request binding | MCP-17 |
| Resource/audience/SSRF validation | MCP-19 |

Normative profile: [CP.5.MCP v3.1](../00-cross-pillar/cp5_mcp_server_security.md)

---

## Open Research Questions

1. How much intended-resource enforcement can a consumer independently verify when the authorization server and MCP server are operated by different parties?
2. What revalidation cadence best detects catalog drift without creating excessive startup or runtime cost?
3. How should clients represent a trusted catalog baseline when extensions dynamically add capabilities?
4. What evidence is sufficient to prove that a state handle is principal-bound without exposing the underlying secret or identifier?
5. How should consumer-side wrappers measure false positives from returned-content sanitization without weakening injection defenses?
6. Which profile requirements can be independently assessed black-box versus requiring operator-supplied evidence?

---

## Research Continuity

The original April 2026 consumer-risk findings remain historical evidence for the need for client-side protection. v3.1 extends that model to the current protocol profile and removes session dependence from the governance claim.

Research Note 023 provides the companion server/profile architecture rationale.

---

## 🔗 Navigation

[Framework Home](../README.md) | [Research 023](./023_mcp-server-security-profile.md) | [CP.5.MCP](../00-cross-pillar/cp5_mcp_server_security.md) | [MCP Toolkit](../examples/mcp-security-toolkit/) | [Scanner](../scanner/README.md)

---

*AI SAFE² v3.1 Research Foundation · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
