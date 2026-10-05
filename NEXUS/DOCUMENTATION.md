# NEXUS Documentation Map

This directory is the canonical home for NEXUS specifications, SDK guidance,
payment controls, integration notes, release records, and governance documents.
NEXUS-owned documentation must remain inside `NEXUS/` so people and agents can
discover the complete implementation from one boundary.

## Choose your path

| I need to… | Start here | Then verify with |
| --- | --- | --- |
| Understand what NEXUS protects | [Overview](README.md) | [Threat model](payments/THREAT-MODEL.md) |
| Install and integrate the SDK | [Python SDK](sdk/python/README.md) | [Examples](examples/) and SDK tests |
| Protect agent-initiated payments | [Payment profile](payments/README.md) | [Gateway](payments/SOVEREIGN-GATEWAY.md) and [controls](payments/CONTROLS.md) |
| Decide whether a deployment is ready | [Deployment readiness](payments/DEPLOYMENT-READINESS.md) | [Sandbox readiness](payments/SANDBOX-READINESS.md) |
| Review security or assurance claims | [Security policy](SECURITY.md) | [Threat model](payments/THREAT-MODEL.md) and [Challenge Lab](payments/CHALLENGE-LAB.md) |
| Extend an adapter or payment rail | [Adapter guide](payments/ADAPTER-GUIDE.md) | [Hardening and extension](payments/HARDENING-AND-EXTENSION.md) |
| Consume NEXUS with an agent | [Agent instructions](AGENTS.md) | [Machine manifest](nexus-docs.manifest.json) and [LLM index](llms.txt) |

## Status legend

Status is always expressed in text; color is supplemental and never carries
meaning by itself.

| Label | Meaning |
| --- | --- |
| **Implemented** | Code exists and its stated behavior is covered by repository tests |
| **Reference** | A working example or contract that still requires deployment-specific controls |
| **Requires binding** | The interface fails closed until an external verifier, signer, store, or rail is connected |
| **Experimental** | Useful for evaluation; compatibility or assurance may change |
| **Not production-assured** | No claim that the complete deployment boundary has passed production acceptance gates |

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
