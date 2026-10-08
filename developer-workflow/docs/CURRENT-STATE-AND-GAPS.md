# Current State and Release Gap

Reviewed: 2026-10-08

## What exists now

| Area | Current capability | Release status |
| --- | --- | --- |
| AI SAFE2 CLI | Consolidated scanning, gates, evidence, decisions, MCP controls, acceptance and self-check | Available; pin 1.0.1 |
| NEXUS | Runtime/distributed trust and enforcement option | Adapter manifest included; deployment-specific integration remains separate |
| Skills | Agent-facing governance and development methods | Supported surface; individual harness installation remains separate |
| Developer Workflow | Existing GitHub pack with risk routing, evidence, and PR templates | Superseded by this provider-neutral contract preview |
| MCP Pro | Public professional MCP product for coding tools | External product surface; adapter contract included |
| Agency Check | Public everyday decision experience and Decision Card model | Deployment in progress; adapter contract included |
| Codex and Claude | Both can continue coding and reviewing | Optional adapters; no configuration takeover |
| Sovereign Runtime | Runtime integration pattern | Adapter placeholder and contract included |
| Drift/Love Equation | Drift and human-alignment evidence source | Adapter placeholder and contract included |

## Gaps before a general-availability release

### Must close after 0.1

1. Implement and test provider execution adapters instead of only manifests.
2. Add signed or otherwise verifiable evidence integrity beyond content hashes.
3. Integrate AI SAFE2 CLI-native evidence manifest and replay commands end to
   end.
4. Define the production Agency Check API/MCP contract and privacy retention
   behavior.
5. Verify MCP Pro entitlement, authentication, rate-limit, and hosted-endpoint
   behavior against the deployed service.
6. Add end-to-end canary repositories for game, mobile, API, and AI-agent
   profiles.
7. Conduct a security review of workflows, untrusted pull-request handling,
   secrets, artifact publication, and adapter execution.
8. Establish upgrade compatibility tests and rollback fixtures.
9. Add an evidence-backed calibration dataset for provider findings.
10. Reconcile public AI SAFE2 version, control-count, licensing, and product
    descriptions before broader marketing.

## 0.1 exit criteria

This preview is ready to share when:

- every JSON file validates and every bundled test passes;
- the game profile can classify representative changes;
- Claude and Codex instructions reference the same policy without changing
  either tool's configuration;
- required evidence cannot be satisfied by `unavailable`, `failed`, or
  `not_requested` results;
- decision records identify the exact revision and remain human-authorized;
- dependency updates enter through isolated pull requests and pinned versions;
- the package contains no secret or production credential.

## Claims boundary

This preview demonstrates structure and executable validation. It does not
establish that every listed adapter is implemented, that a project is secure,
or that any organization is compliant or certified.

