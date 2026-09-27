# Policy Parity Guard

**Human name:** Policy Parity Guard

**Technical name:** `ParityEnforcedPolicyAuthority`

**Profile:** CP.5.APAY policy-deployment integrity extension

**Status:** Draft reference standard; not a production assurance claim

## Purpose

A policy name is not proof that the intended rules ran. Policy Parity Guard
requires the independently deployed evaluator and the NEXUS reference firewall
to evaluate the same authoritative input and agree before an ALLOW result can
carry signing authority. Neither result wins a disagreement; divergence denies.

## Normative requirements

| ID | Required outcome |
| --- | --- |
| PPG-01 | The deployed evaluator runs outside the agent and model trust boundary. |
| PPG-02 | The exact input document is content-addressed and bound into the deployed response. |
| PPG-03 | The policy identifier and immutable bundle digest match pinned deployment configuration. |
| PPG-04 | The evaluator identity is allowlisted and the response is authenticated independently of agent claims. |
| PPG-05 | The response is fresh, timezone-aware, and neither stale nor future-dated. |
| PPG-06 | Decision, complete reason-code set, policy identifier, and consequence match the reference result. |
| PPG-07 | Unknown values, duplicate reason codes, malformed proof, outage, or timeout deny signing authority. |
| PPG-08 | A divergence result contains no canonical transaction or policy authorization receipt. |
| PPG-09 | Policy bundle identity is included in the policy snapshot trusted by Key Guardian. |
| PPG-10 | Parity evidence contains digests and control outcomes, not raw credentials or unnecessary payment payloads. |

Probabilistic policy comparison is not sufficient for credential release. A
deployment may use sampling in observe-only rollout, but an enforced transaction
must receive exact deterministic agreement. Human approval cannot override a
failed parity check because the failure concerns which rules actually ran.

## Deployment boundary

The reference contracts deliberately do not ship a permissive network client.
Production operators must inject an authenticated evaluator transport with
protected trust roots, bounded timeouts, an independently verifiable response,
and a bundle provenance process. `REFERENCE` assurance and synthetic evaluators
are conformance evidence only; they are not proof of a live OPA deployment.
