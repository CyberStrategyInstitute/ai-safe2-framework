# AISM Technology Card template

[Framework Home](../../README.md) | [AISM](../../AISM/README.md) | [Technology Profile](../TECHNOLOGY-CONTRIBUTION-PROFILE.md) | [Evidence Assurance](../EVIDENCE-ASSURANCE.md)

Copy this template for one artifact/version and assessment boundary. This is a
Markdown review record under proposed AISM-TCP v1.0, not a CLI assessment payload.
Replace placeholders; preserve `not_assessed`, unknowns, and reasons for N/A.

## Identity and scope

- Technology/artifact:
- Artifact type: product / technique / paper / benchmark / investigation / accountability event
- Owner and exact version/commit:
- Artifact date and assessment date:
- Assessor and relationship to producer:
- Claimed function:
- Source URLs/artifacts and actual review dates:
- System identity and deployment boundary:
- Enforcement planes and excluded paths:
- OS/kernel/cloud/service dependencies:

## Claim and control register

| Claim ID | Exact claim | Canonical control ID/name and document | Effect | Coverage and denominator | Evidence artifact/version | Assurance v1.0 rating/status | Origin and independence | Limits/contradictions |
|---|---|---|---|---|---|---|---|---|
| claim-01 | [required] | [required] | addresses / implements / enforces / validates / evidences / challenges | full / partial / none / unknown / not_applicable; explain | [required] | E0-E5 or not_assessed | author-reported / reviewer-observed / independently evaluated | [required] |

List addressed, implemented, enforced, validated, merely evidenced, and challenged
controls separately through the effect column. Each asserted effect needs evidence.

## Pillar contribution

| Pillar | Contribution 0-5 or no score | Status | Supporting claim IDs | Covered scope | Reason and gaps |
|---|---|---|---|---|---|
| P1 Shield | | not_assessed | | | |
| P2 Ledger | | not_assessed | | | |
| P3 Circuit Breaker | | not_assessed | | | |
| P4 Command Center | | not_assessed | | | |
| P5 Learning Engine | | not_assessed | | | |

- Cross-pillar controls and effects:
- Maximum supported contribution and exact boundary (no overall maturity score):
- Organizational maturity assessment reference, if separately assessed:

## Mechanism, testing, and authority

- Interception/enforcement location and who can bypass or alter it:
- Deterministic interception:
- Authorization judgment (deterministic / probabilistic / mixed / unknown):
- Deterministic actuation:
- Testing scope, harness/version, clean/attacked pairs, and reviewable results:
- Positive and negative cases; side-effect observation:
- Legitimate-task completion, false blocks, latency, cost, and denominators:
- Independent replication, evaluator, and conflicts (or not established):
- Challenge Lab claim maturity, if separately assessed:
- Known bypasses and uncovered dependencies:
- Failure behavior on outage/timeout/restart/revocation:
- Fail-open / fail-closed / fail-safe / unknown, with evidence:
- Organizational authority retained: inspect / configure / revoke / replace / export
- Named stopping authority and evidence of intervention:
- Required complementary controls:
- Retention, incident evidence, and notification owner:

## Decision and claims

- Verdict: supports / refines / challenges / conflicts, with rationale
- Adoption: adopt / pilot / hold / reject, conditions, and decision owner
- Residual risks and unresolved facts:
- Permitted claim (include version, scope, assurance rubric, and source):
- Prohibited overclaim:
- Acceptance tests before adoption:
- Rollback/withdrawal path:
- Review date and triggers (version, policy, dependency, incident, or bypass change):
