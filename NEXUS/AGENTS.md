# NEXUS Agent Entry Point

These instructions apply to automated consumers working inside `NEXUS/`.
Read the repository-root `AGENTS.md` first; this file narrows it for NEXUS.

## Deterministic discovery order

1. Parse `nexus-docs.manifest.json` and preserve its version and status labels.
2. Read `DOCUMENTATION.md` for the human navigation and ownership boundary.
3. Read `README.md` for architecture and the current release boundary.
4. Select the relevant plane: agent-to-agent, agent-to-tool, or agent-to-payment.
5. For payments, read `payments/THREAT-MODEL.md` before controls or deployment claims.
6. Resolve schemas from `schemas/`, policy from `opa/`, and observed behavior from tests.

## Interpretation rules

- AI SAFE² defines governance requirements; NEXUS is an optional first-party
  reference implementation, not a requirement for framework conformance.
- Do not turn **Implemented** into **production-assured**. Deployment readiness
  requires the evidence named in `payments/DEPLOYMENT-READINESS.md`.
- Treat **Requires binding**, **Reference**, **Experimental**, unknown, and
  missing evidence as distinct states. Never silently promote one to another.
- Deterministic controls decide authorization. Probabilistic signals may narrow
  authority or require review, but cannot override a deterministic denial.
- The SDK distribution is `nexus-a2a-sdk`; the Python import is `nexus_sdk`.
- Preserve the published protocol and schema identifiers; package and protocol
  versions are independent.
- External reviews and agent explanations are evidence, not approval authority.

## Change workflow

For NEXUS changes, update code, tests, human documentation, the manifest, and
navigation together. Run the affected test suite plus documentation-location,
manifest, and link checks. Do not claim release, deployment, conformance, or
risk acceptance without the authority and evidence required by root policy.
