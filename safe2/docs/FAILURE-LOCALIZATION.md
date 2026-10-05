# Failure Localization

`safe2 evidence diagnose` turns source-attributed failure observations into a
ranked, provider-neutral diagnostic record. It helps a person or agent decide
where to investigate and who should own the next action without presenting a
candidate explanation as a proven root cause.

## Why It Exists

An agent system is more than its model. A failure can arise in the harness,
tool, skill, memory, environment, policy, evaluator, or an interaction between
them. Model-only attribution hides those boundaries and makes repairs harder to
reproduce. Failure localization binds every candidate to the complete system
identity that was assessed.

## Quick Start

First create a system identity manifest:

```bash
safe2 evidence system safe2/data/system-identity-source-demo.json \
  --output system-identity.json \
  --strict
```

Then diagnose the failure evidence:

```bash
safe2 evidence diagnose safe2/data/failure-source-demo.json \
  --system-identity system-identity.json \
  --output failure-diagnosis.json \
  --card failure-card.md \
  --strict
```

The JSON artifact is the canonical agent exchange format. The Markdown card is
a human-readable view of the same record. `--strict` exits with status `1` when
there is no unique leading candidate supported by strong or moderate evidence;
the diagnostic artifact is still written so the uncertainty is reviewable.

## Evidence Levels

| Level | Meaning |
|---|---|
| `strong` | At least two direct, observed supporting facts from distinct sources, no observed contradiction, and no stated assumption |
| `moderate` | At least one direct, observed supporting fact and no observed contradiction |
| `limited` | Support is indirect or declared rather than directly observed |
| `insufficient` | The available observations do not support the candidate |
| `contradicted` | At least one observed fact contradicts the candidate |

These levels are deterministic evidence classifications, not probabilities.
Candidate ranking favors stronger, more direct, and more independently sourced
support and exposes contrary evidence rather than suppressing it. A tie remains
`competing_candidates`; unsupported candidates produce
`insufficient_evidence`.

## Evidence Boundaries

The command always records:

- `decision_scope: failure_localization_support_only`
- `root_cause_verified: false`
- `probability_estimate: false`
- `conformance_claim: false`

It does not execute a task, inspect an agent invisibly, prove causation, assign
fault, verify billing, authorize a repair, or establish AI SAFE² conformance.
Every observed or declared fact must identify its source. Missing evidence must
remain explicitly missing and cannot carry a source reference that implies an
observation occurred.

## Integration Pattern

Codex, Claude Code, Hermes, OpenClaw, CI systems, and other harnesses can emit
the same `safe2.failure-source.v1` contract. Native records should remain
available and be named in `source_ref`; the normalized record is a translation
layer, not a replacement for provider evidence.

Recommended workflow:

1. Capture the full system with `safe2 evidence system`.
2. Preserve task, tool, test, policy, environment, usage, and human-report
   observations with stable source identifiers.
3. Declare competing candidates, their assumptions, contradictions, repair
   owner, and actionable next check.
4. Run `safe2 evidence diagnose` and retain both source and result hashes.
5. Perform the recommended check, append new observations, and rerun rather
   than editing history to manufacture certainty.

Challenge Lab experiments can bind this diagnostic artifact into later
evidence bundles. The capability does not change Challenge 001 scenarios,
expected outcomes, or third-party harness semantics.

## Privacy and Safety

Do not place secrets, credentials, private prompts, or unnecessary personal
data in observations. Prefer identifiers, digests, redacted summaries, and
references to access-controlled native evidence. Treat candidate descriptions
as untrusted claims until corroborated by direct observations.

## Contracts and Examples

- Source contract: `safe2.failure-source.v1`
- Diagnostic contract: `safe2.failure-diagnosis.v1`
- Example source: `safe2/data/failure-source-demo.json`
- Human output: the optional Failure Localization Card

Use `safe2 schema export failure-source-v1` and
`safe2 schema export failure-diagnosis-v1` to retrieve the packaged JSON
Schemas.
