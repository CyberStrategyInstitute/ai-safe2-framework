# Deployment Proof & Readiness

**Human name:** Deployment Proof & Readiness

**Technical name:** `DeploymentReadinessAuthority`

**Profile:** CP.5.APAY production-admission extension

**Status:** Draft reference standard; not a production assurance claim

## Purpose

Component tests and a successful sandbox run do not, by themselves, prove that
the exact production deployment is safe to activate. Deployment Proof &
Readiness converts authenticated operational evidence into one short-lived,
signed, fail-closed decision that a human or agent can verify without trusting
the agent requesting activation.

The authority does not deploy software, move money, or turn a rail on. It sets
the maximum permitted mode. A failed assessment permits only `disabled`; a
complete assessment may permit `enforced`, subject to separate deployment
change control.

## Normative requirements

| ID | Required outcome |
| --- | --- |
| DPR-01 | Evidence binds the exact deployment, environment, software, configuration, policy-parity, and sandbox-profile digests. |
| DPR-02 | The complete execution plane reports deployment assurance with no missing or reference-only component. |
| DPR-03 | Sandbox Rail Readiness independently permits enforced mode and its exact report is bound into the evidence set. |
| DPR-04 | Every required control has exactly one explicit passing result; missing, duplicate, conflicting, malformed, or false evidence fails readiness. |
| DPR-05 | Evidence is fresh, authenticated by a deployment-assured verifier, and produced by allowlisted assessors. |
| DPR-06 | At least two distinct assessors contribute; assessors cannot also be deployment approvers. |
| DPR-07 | Accountable and security owners are named and separated; data ownership and jurisdiction are declared. |
| DPR-08 | Operational proof covers state and evidence restore, evidence completeness, revocation, ambiguous recovery, bypass prevention, monitoring, and incident escalation. |
| DPR-09 | Evidence lifecycle proof covers export, deletion, and legal hold. |
| DPR-10 | An allowlisted change approver authorizes the assessment and an independently protected authority signs the result. |
| DPR-11 | A refusal is signed as evidence; an unavailable signer never yields an unsigned readiness decision. |
| DPR-12 | Decisions are short-lived and expose digests and findings, not payment payloads, credentials, or account details. |

## Required control identifiers

`DEFAULT_DEPLOYMENT_CONTROLS` defines the baseline set. Operators may replace it
with a stricter governed set, but must not silently remove controls from a
previously approved profile. Profile changes create a new profile digest and
invalidate old evidence.

The baseline covers execution readiness, live policy parity, Key Guardian
isolation, independent runtime verification, state and evidence recovery,
evidence completeness, revocation and ambiguous-state drills, sandbox
readiness, network bypass prevention, monitoring and escalation, evidence
export/deletion/legal hold, data residency, and accountable ownership.

## Verification flow

1. Construct a versioned `DeploymentReadinessProfile` with content-addressed
   identities, owners, jurisdiction, trusted assessors, and approvers.
2. Collect one authenticated `DeploymentControlEvidence` item per required
   control. Evidence contains results and digests only.
3. Supply the current `GatewayReadiness` and `SandboxReadinessReport` objects.
4. Call `DeploymentReadinessAuthority.assess(...)` with the authorized change
   approver identity.
5. Independently verify the returned decision digest, proof, expiry, profile
   digest, mode, and findings before any activation mechanism can proceed.
6. Reassess after software, configuration, policy, sandbox profile, ownership,
   jurisdiction, trust roots, or required controls change.

## Security, privacy, governance, and sovereignty

The profile makes agent self-approval, evidence replay across deployments,
single-assessor promotion, and substitution of a different gateway or sandbox
report deterministic failures. It leaves the operator in control of assessors,
approvers, owners, jurisdiction, retention, trust roots, and activation.

Reports intentionally retain only identities, timestamps, content digests,
control findings, and a decision proof. Payment payloads, unrestricted keys,
credentials, and account details remain outside the readiness artifact. A
deployment must separately protect evidence at rest, signing keys, verifier
channels, and the change-control mechanism.
