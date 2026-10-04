# NEXUS Documentation Map

This directory is the canonical home for NEXUS specifications, SDK guidance,
payment controls, integration notes, release records, and governance documents.
NEXUS-owned documentation must remain inside `NEXUS/` so people and agents can
discover the complete implementation from one boundary.

## Start here

- [NEXUS overview and installation](README.md)
- [Python SDK](sdk/python/README.md)
- [Changelog](CHANGELOG.md)
- [NEXUS v0.5.0 release notes](RELEASE-NOTES-v0.5.0.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## Sovereign Payment Gateway

- [Payment integrity profile](payments/README.md)
- [Sovereign Payment Gateway](payments/SOVEREIGN-GATEWAY.md)
- [Controls](payments/CONTROLS.md)
- [Threat model](payments/THREAT-MODEL.md)
- [Deployment proof and readiness](payments/DEPLOYMENT-READINESS.md)
- [Policy parity](payments/POLICY-PARITY.md)
- [Recovery](payments/RECOVERY.md)
- [Sandbox readiness](payments/SANDBOX-READINESS.md)
- [Challenge Lab](payments/CHALLENGE-LAB.md)

## Protocol, policy, and assurance

- [Architecture and protocol overview](README.md#architecture)
- [Compliance material](compliance/)
- [OPA policies](opa/)
- [Schemas](schemas/)
- [Governance](governance/GOVERNANCE.md)

## Integration guidance

- [Examples](examples/)
- [Legacy sovereign-runtime integrations](integrations/legacy-sovereign-runtimes/)

The legacy runtime pages describe older AI SAFE² shared-engine examples. They
are retained for discovery and migration context, but they are not claims that
those example engines implement the current NEXUS SDK or payment gateway.

## Repository boundary

The repository-level `docs/` directory remains the home of shared AI SAFE²,
AISM, CLI, evidence, and engineering documentation. A shared document may link
to NEXUS without becoming NEXUS-owned. A document whose primary title or subject
is NEXUS belongs under this directory.

Challenge-local NEXUS treatment material may remain beside the challenge that
executes it because its path is part of the challenge evidence boundary. Those
exceptions must link back to this documentation map and must not become a second
general-purpose NEXUS documentation tree.
