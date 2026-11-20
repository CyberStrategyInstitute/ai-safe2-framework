# CP.5.MCP v3.5 | current-condition and outcome requirements

Candidate profile. The nineteen v3.1 IDs and protocol bindings are retained. Twelve distinct child clauses deepen the requirements; shared clauses can support more than one profile control. Apply core CP.11-CP.15, F3.6-F3.7 and A2.7-A2.9 wherever applicable.

## MCP-1 Command Construction Safety

Prevent unsafe executable command construction from untrusted tool arguments.

## MCP-2 Return-Path Content Sanitization

Treat tool output as untrusted content and inspect it before model-context entry.

- **MCP-R05** Returned content and generated parameters cannot widen grants. Exercise each enabled input modality and destination validator.
## MCP-3 Least-Privilege Tool Exposure

Expose only explicitly authorized tools and resources to each verified principal.

## MCP-4 Server and Binary Integrity

Verify local binaries before spawn and remote endpoint identity before protected use.

- **MCP-R03** Trust must precede startup, install hooks and credential access where the client can enforce it. Test pre-trust effects.
## MCP-5 Tool Invocation Audit

Emit attributable and independently reconstructable evidence for protected tool invocations.

- **MCP-R09** Retries preserve bound action identity and verified outcome. Test timeout after an external commit.
- **MCP-R11** Separate invocation, acceptance and observed postcondition in the evidence. Test false tool success.
## MCP-6 Input Validation

Validate tool input against the authorized schema and policy before dispatch.

- **MCP-R05** Returned content and generated parameters cannot widen grants. Exercise each enabled input modality and destination validator.
- **MCP-R10** Revalidate resolved destination and environment at use. Test redirect, account and resource substitution.
## MCP-7 Trust Establishment

Establish a verified principal and policy context before protected tool use.

- **MCP-R01** Discovery and fallback cannot reduce identity or resource checks. Test missing discovery and unauthorized fallback.
- **MCP-R03** Trust must precede startup, install hooks and credential access where the client can enforce it. Test pre-trust effects.
## MCP-8 Economic Ceiling

Attribute consumption to a principal and fail closed at the authorized ceiling.

- **MCP-R06** Aggregate concurrent work and outstanding commitments under the inherited task ceiling. Test individually permitted child requests that exceed the whole budget.
## MCP-9 Secret Boundary

Keep secrets out of model context, untrusted output, arguments, and inappropriate logs.

- **MCP-R12** Tool, tenant and purpose boundaries survive service credential use. Test fallback to shared operator authority.
## MCP-10 Delegation Edge Monitoring

Preserve originating delegation lineage across agent-to-tool actions.

- **MCP-R06** Aggregate concurrent work and outstanding commitments under the inherited task ceiling. Test individually permitted child requests that exceed the whole budget.
- **MCP-R08** Revocation reaches cached grants, descendants and queued work. Record unreachable resources and isolate their effects.
## MCP-11 Catalog Provenance

Compare catalogs against an authorized provenance baseline at trust establishment and revalidation.

- **MCP-R04** Catalog, schema and effective-permission changes invalidate affected approvals. Test a signed change that expands authority.
## MCP-12 Principal-Scoped State

Bind durable or handle-scoped state to the verified principal and policy context.

- **MCP-R07** State handles retain principal, tenant, scope, expiry and correction lineage. Test transfer and restored stale state.
## MCP-13 Revocation and Reauthorization

Invalidate prior authorization after revocation or material policy change without relying on a transport session boundary.

- **MCP-R08** Revocation reaches cached grants, descendants and queued work. Record unreachable resources and isolate their effects.
## MCP-14 Extension Capability Negotiation

Permit extensions only when included in the principal capability grant and recorded at trust establishment.

## MCP-15 Header Body Assertion Integrity

Reject disagreement between Mcp-Method or Mcp-Name headers and the JSON-RPC body before dispatch.

## MCP-16 State Handle Binding and Lifecycle

Require unguessable, expiring, principal-bound state handles and never treat possession alone as identity.

- **MCP-R07** State handles retain principal, tenant, scope, expiry and correction lineage. Test transfer and restored stale state.
## MCP-17 MRTR Round-Trip Integrity

Bind model-mediated tool responses to the originating request and reject replay or mismatched responses.

- **MCP-R09** Retries preserve bound action identity and verified outcome. Test timeout after an external commit.
## MCP-18 Catalog Cache Integrity

Bound cache TTLs, bind cache keys to trust context, and detect catalog or schema provenance drift during revalidation.

- **MCP-R04** Catalog, schema and effective-permission changes invalidate affected approvals. Test a signed change that expands authority.
## MCP-19 Authorization Chain Integrity

Validate issuer, intended resource or audience, authorization metadata, redirect or resource binding, and SSRF boundaries before protected state change.

- **MCP-R01** Discovery and fallback cannot reduce identity or resource checks. Test missing discovery and unauthorized fallback.
- **MCP-R02** Bind inbound principal, intended resource and delegated purpose. Reject a valid token for the wrong resource.
- **MCP-R10** Revalidate resolved destination and environment at use. Test redirect, account and resource substitution.
- **MCP-R12** Tool, tenant and purpose boundaries survive service credential use. Test fallback to shared operator authority.

[v3.1 compatibility specification](cp5_mcp_server_security.md) | [Cross-Pillar Governance](README.md) | [Framework Home](../README.md)
