# NEXUS v0.5.0 — Sovereign Payment Gateway

NEXUS v0.5.0 gives builders a safer boundary for agent-initiated payments. An
agent may propose a purchase, but it cannot silently expand its authority,
obtain unrestricted payment keys, replay an approval, restore spent capacity,
or decide for itself that money moved.

## Why use it

Agent identity and a valid signature are not enough when the agent host may be
compromised. NEXUS adds deterministic checks at the point of value movement:

- payment authority and cumulative exposure are enforced atomically;
- payment credentials remain behind **Key Guardian**, an isolated signing
  boundary that never returns raw keys;
- policy, runtime integrity, human intent, and settlement truth can be operated
  as independent authorities;
- approvals are bound to the exact transaction rather than a vague session;
- retries, recovery, and revocation fail closed and leave reconstructable
  evidence; and
- deployment readiness identifies missing production bindings instead of
  presenting a reference component as production assurance.

This raises the cost of fraud and agent compromise while keeping the normal
user experience simple: clear decisions by default, and immediate evidence when
a person, investigator, or auditor needs to understand what happened.

## Install

```bash
python -m pip install nexus-a2a-sdk==0.5.0
```

```python
import nexus_sdk
from nexus_sdk.payments import NEXUSPaymentExecutionPlane

assert nexus_sdk.__version__ == "0.5.0"
```

The published distribution is named `nexus-a2a-sdk`; the Python import is
`nexus_sdk`.

## What is included

- Sovereign Payment Gateway execution plane
- Key Guardian credential-use boundary
- durable authority, replay, settlement, and evidence contracts
- independent policy and runtime-attestation authorities
- transaction-bound human-intent verification
- authoritative settlement observation
- governed recovery and policy-parity checks
- rail adapter readiness and deployment-proof decisions

## Compatibility

The release retains the `CP.5.APAY/0.4` profile, schemas, policy identifiers,
and wire contracts. v0.5.0 composes and hardens that foundation; it does not
silently introduce an incompatible protocol revision.

## Production boundary

NEXUS is a reference implementation, not a certification or automatic claim of
production safety. Before moving real value, operators must supply durable
production storage, protected signing or HSM-backed credentials, authenticated
payment-rail integrations, independently controlled trust roots, monitoring,
operational governance, and the deployment evidence identified by the readiness
API.

Start with the [NEXUS guide](https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/nexus-v0.5.0/NEXUS), the [Sovereign Payment Gateway contract](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/nexus-v0.5.0/NEXUS/payments/SOVEREIGN-GATEWAY.md), and [Deployment Proof & Readiness](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/nexus-v0.5.0/NEXUS/payments/DEPLOYMENT-READINESS.md).

Security issues should be reported through the repository's [security policy](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/nexus-v0.5.0/NEXUS/SECURITY.md), not a public issue.
