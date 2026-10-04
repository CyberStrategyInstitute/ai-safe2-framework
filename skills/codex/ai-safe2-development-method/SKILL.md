---
name: ai-safe2-development-method
description: Plan and execute material repository changes with the AI SAFE2 development method. Use when a coding task needs a delivery-shape decision, risk-adjusted design depth, isolated implementation, test-first or explicit substitute evidence, systematic debugging, review cadence, before/after comparison, or a completion receipt. Do not use for read-only explanations, trivial edits, or as authority to merge, release, deploy, accept risk, or change policy.
---

# AI SAFE2 Development Method

Convert software-development discipline into decision evidence. Keep policy,
implementation, verification, semantic review, and human authority separate.

## Workflow

1. Read the nearest repository instructions and current policy before acting.
2. Classify delivery shape independently from risk:
   - `spike`: disposable learning; implementation does not become production output.
   - `bounded`: limited scope with explicit acceptance conditions and exclusions.
   - `architectural`: cross-boundary or durable design requiring a written spec and plan.
3. Create a `safe2.development-plan-source.v1` source and run
   `safe2 dev plan SOURCE --output PLAN`. Use the repository policy when present.
4. If the plan is `review_required`, pause only for the named missing decision.
   Low- and medium-risk bounded work may proceed under existing user authority.
   Never work around an `invalid` plan.
5. Isolate repository-changing work. Preserve unrelated user changes.
6. Use the selected evidence mode:
   - code: observe a failing behavior first, then the passing behavior;
   - existing ambiguous behavior: characterize before changing it;
   - contracts/configuration: establish the invalid/valid boundary first;
   - documents/UI: use render or interaction validation;
   - spike: record the hypothesis, result, and discard decision.
7. When a check fails, localize the cause before proposing a fix. Do not stack
   speculative changes. Re-run the smallest affected check after each fix.
8. Review at the cadence in the plan. Treat PR-Agent, Greptile, and other model
   reviewers as attributed evidence. Provider failure is `unavailable`, not pass.
9. Capture comparable before/after evidence when required. If no safe baseline
   exists, preserve that gap and add a regression test without claiming a direct delta.
10. Before any completion claim, run fresh verification against the final revision
    and produce `safe2 dev receipt PLAN SOURCE --artifact-root ROOT --output RECEIPT`.

## Decision Rules

- Delivery shape controls design depth; risk controls scrutiny and authority.
- Architectural work and high/critical risk require explicit human design approval.
- Critical risk requires a threat model and specialist review cadence.
- A spike is disposable. Reusable output requires a bounded or architectural plan.
- Deterministic checks remain authoritative. Semantic reviewers explain and
  corroborate; they do not replace tests, schemas, scanners, or human decisions.
- Never infer permission to merge, release, deploy, change policy, access secrets,
  or accept residual risk from a plan or receipt.

## References

- `references/method.md`: classification, debugging, evidence, and receipt guidance
- `references/evaluation.md`: pressure cases and regression expectations
