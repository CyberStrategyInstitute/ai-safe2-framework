# Sandbox Rail Readiness

**Human name:** Sandbox Rail Readiness

**Technical name:** `SandboxRailReadinessGate`

**Profile:** CP.5.APAY rail-activation extension

**Status:** Draft reference standard; not a production assurance claim

## Purpose

Passing synthetic unit tests does not authorize real payment traffic. Sandbox
Rail Readiness converts authenticated, negative-path sandbox results into a
deterministic maximum activation mode: disabled, observe-only, or enforced.
The agent cannot promote its own rail and the gate never moves value.

## Normative requirements

| ID | Required outcome |
| --- | --- |
| SRR-01 | Evidence binds the exact RailGuard contract, binding implementation, policy stack, and execution profile digests. |
| SRR-02 | Evidence is authenticated by a pinned observer and comes from allowlisted sandbox counterparties. |
| SRR-03 | At least two independent counterparties and environments pass before enforced mode is eligible. |
| SRR-04 | Required cases cover positive binding, mutation, replay, downgrade, revocation, timeout, reconciliation, settlement, and failure release. |
| SRR-05 | Every required outcome is explicitly `true`; missing, duplicate, malformed, or false outcomes fail readiness. |
| SRR-06 | Sandbox runs use no production credential and move no real value. |
| SRR-07 | Evidence is fresh, bounded in duration, payload-minimized, and content-addressed. |
| SRR-08 | Duplicate identical runs are idempotent; conflicting evidence for one run blocks enforcement. |
| SRR-09 | The complete gateway execution plane must independently report deployment-ready before enforced mode. |
| SRR-10 | The result is a maximum permitted mode, not an automatic production activation. |

One authenticated passing run permits at most observe-only operation. Failed or
untrusted evidence cannot be outvoted by successful runs in the same readiness
set. An operator must separately authorize any mode change through deployment
change control, and must return to a lower mode when pinned code, policy,
counterparty behavior, or execution configuration changes.

## Privacy and sovereignty

Reports contain run and component digests, named case outcomes, counterparties,
environments, and findings. They omit payment payloads, credentials, account
details, and agent-generated explanations. Operators choose their trusted
counterparties, observers, retention, jurisdiction, and production activation;
the profile does not delegate those decisions to a rail vendor.
