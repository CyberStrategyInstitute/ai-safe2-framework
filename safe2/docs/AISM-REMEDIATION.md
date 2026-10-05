# AISM Implementation Decisions and Remediation

AI SAFE² CLI 0.8.0 translates an existing AISM assessment into a traceable,
human-owned improvement plan. It binds the plan to the exact assessment,
agent-system identity, and deployment-scope artifacts under review.

The workflow does not invent recommendations. Operators supply proposed
actions and their rationale. The CLI validates whether each action traces to
applicable controls, AISM cells, available evidence, stated assumptions, an
accountable owner, dependencies, alternatives, impacts, exit criteria, and
residual risk.

## Quick start

Create a bound source template:

```bash
safe2 aism remediation-init assessment.json \
  --system-identity system-identity.json \
  --assessment-scope assessment-scope.json \
  --decision-owner "Accountable system owner" \
  --output remediation-source.json
```

Populate the source with proposed actions, then build canonical JSON and a
human decision card:

```bash
safe2 aism plan remediation-source.json assessment.json \
  --system-identity system-identity.json \
  --assessment-scope assessment-scope.json \
  --output remediation-plan.json \
  --card remediation-card.md \
  --strict
```

For reassessment, preserve the prior canonical plan and supply it explicitly:

```bash
safe2 aism plan remediation-source-next.json assessment-next.json \
  --system-identity system-identity-next.json \
  --assessment-scope assessment-scope-next.json \
  --previous remediation-plan.json \
  --output remediation-plan-next.json \
  --card remediation-card-next.md \
  --strict
```

## Decision meanings

| Gate | Meaning |
|---|---|
| `hold` | Unsafe or ambiguous scope, a critical assessment conflict, a blocked action, or a prior completion regression requires resolution |
| `review` | Gaps, uncovered cells, or open actions remain |
| `ready_for_human_decision` | No supplied gap or open action remains; the named human may decide what to do |

Every plan retains `remediation_authorized: false` and
`conformance_claim: false`. A decision card is a projection of canonical JSON,
not a separate source of truth.

## Evidence boundaries

- The raw AISM Sovereignty Score remains normative.
- Remediation status never increases the assessment score automatically.
- A completed action requires completion evidence available within the bound
  assessment, identity, or scope record.
- Evidence identifiers establish traceability, not authenticity or truth.
- Accepted residual risk must retain its owner, rationale, review date, and
  evidence references.
- Alternatives remain visible so a recommendation does not erase why another
  path was rejected.
- The CLI validates the supplied plan; it does not execute remediation, approve
  deployment, accept risk, certify an organization, or claim AI SAFE²
  conformance.

## Contracts

- `aism-remediation-source-v1`
- `aism-remediation-plan-v1`

Use `safe2 schema list`, `safe2 schema export`, and `safe2 schema validate` to
integrate the contracts into agent harnesses, CI workflows, or governance
systems.
