# feat(cli): 0.3.0 task receipts, usage evidence, and fresh pytest capture

## Summary

Adds a local evidence workflow for declared task outcomes and resource use. This is a new update after merged PR #317, not an amendment to that release.

## Changes

- Eight feedback commands: receipt, usage, import-junit, capture-process, capture-pytest, verify-pytest, sign-report, verify-report.
- Seven versioned contracts: task input, task receipt, test result, tool result, report attestation, usage summary, pytest capture.
- Artifact digest checks, contextual report binding, conservative supported/contradicted/unverifiable assessments, and readable Markdown receipts.
- Explicit bounded local execution; fresh pytest XML association; offline semantic consistency checking.
- Expiring detached Ed25519 test/tool report signatures with external trusted keys.
- Declared task usage correlation, parent-cycle detection, duplicate-event ownership rejection, and separate reported/estimated/unknown quantities.
- Shared process capture completeness tracking, adversarial regression tests, packaged examples, and LF-stable demo fixtures.
- Root/CLI documentation, task-receipt guide, release notes, and held announcement copy.
- Reusable GitHub release-note template with outcome-first sections, copy-safe tables, quick start, evidence boundaries, and roadmap separation.
- CLI version 0.3.0 and an installed-distribution workflow in the Python 3.11–3.14 CI matrix.

## Validation

- Windows Python 3.12: 687 passed, 5 skipped across `tests/` and `scanner/tests/`, including the provider-feedback regression cases.
- Capture/verifier regression suite: 22 passed on each of Python 3.11–3.14 in the preceding verification pass.
- Source distribution built; wheel built from that source distribution.
- Installed wheel smoke test passed outside checkout imports: receipt, all seven contracts, actual synthetic pytest capture, and offline verification.
- Targeted lint, repository UX, and agent-manifest checks passed.
- Hosted Linux CI remains a required pre-merge check, not a locally established result.

## Security and compatibility

Participant feedback closed through documentation and three regression cases:
nonsynthetic declarations, preserved outage disagreement with observed/missing
state, and rejection of unimplemented adapter contracts. The existing challenge,
grader, reference outcomes, and contract enum remain unchanged. See
`docs/CHALLENGE-PROVIDER-FEEDBACK.md`. No participant execution or ledger proof
was independently verified; no provider-specific accommodation was introduced.

No framework control count change: 161 core controls, CP.1–CP.10, UAS as a separate 27-requirement profile. No conformance or AISM score inferred.

Local child execution is not isolated; source/environment labels are declarations. Unsigned bundles can be rewritten. Authentication proves bytes/key association, not execution truth. Usage is not reconciled billing. No universal harness hooks, new SkillSpector fix, or Headroom adapter is claimed.

Existing friction commands are retained. Release publication remains manual: review hosted checks, merge, then publish release notes. The repository's published-release workflow also publishes the package to PyPI; do not trigger it as a documentation-only step.
