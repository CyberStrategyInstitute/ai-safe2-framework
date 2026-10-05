# AI SAFE² Challenge CLI Validation

Evidence-backed handoff for fixture, translation, and controlled execution stages.

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../../README.md)
[![Review](https://img.shields.io/badge/Review-Offline_Evidence-820F1A?style=flat-square)](./CHALLENGE-CLI.md)

[Framework Home](../../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [AISM](../../AISM/) | [NEXUS](../../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

[User guide](./CHALLENGE-CLI.md) | [Design](./CHALLENGE-HARNESS-DESIGN.md) | [Implementation](../challenge/README.md)

---

## CLI 0.9 controlled-execution addendum

Local release-candidate validation completed on 2026-09-26 at revision
`9484487` using a clean detached worktree. This addendum covers the new bounded
Challenge 001 process seam; the CLI 0.2 fixture record below remains historical.

| Check | Observed result and boundary |
|---|---|
| Clean full CLI/scanner suite | 823 passed, 7 skipped on Windows with Python 3.12.14 |
| Focused compatibility matrix | 24 passed on each of Python 3.11.15, 3.12.14, 3.13.14, and 3.14.6 |
| Negative execution cases | Invalid JSON, timeout, and output-cap cases remained explicit incomplete episodes |
| Installed wheel acceptance | CLI 0.9.0 wheel exposed both new schemas and verified the packaged controlled-executor example outside the checkout |
| Build contents | Wheel contains the plan/receipt contracts and packaged executable example; source and wheel artifacts built successfully |
| Static/repository gates | Release-critical Ruff, agent manifest, repository UX, example index, changed-document Markdown, and diff checks passed |
| Hosted and independent review | Pending on the exact pushed revision; local results do not substitute for GitHub checks or external review |

The pre-registration binds the interpreter/executable and each argument that is
a regular file at planning time. Execution rechecks those files before the first
scenario and records before/after hashes. The receipt binds the plan, source,
normalized run, optional system identity, and per-episode request/response hashes.
Verification detects cross-artifact substitution, ordinary receipt tampering, and
resealed inconsistent file checks without re-running the provider.

The remaining boundary is deliberate and release-visible: the direct child has
time and combined-output limits, but it runs with current-user authority and the
portable runner does not establish network/filesystem sandboxing or descendant
process-tree containment. Provider identity and observations remain declarations;
matching results do not establish independent replication. Use a separately
isolated environment and external stop controls for untrusted or real targets.

## Decision and scope

Local validation completed on 2026-09-09 using Windows and Python 3.12.14 for CLI 0.2.0.
The offline fixture and translation workflow is ready for repository review.
It is **not** evidence that a live harness, TENIR deployment, or business system
has been validated. No numeric quality rating or framework certification is claimed.
No release or third-party integration was published by this validation run.

## Checks performed

| Check | Result and boundary |
|---|---|
| Full CLI/scanner regression suite | 496 passed, 2 skipped on this Windows host; pre-quickstart baseline was 458 passed, 2 skipped |
| New Challenge tests | Runner/grader, imports, comparisons, signing, path and JSON safety, CLI reports, and AISM integration exercised |
| Static correctness/style | Ruff passed on the new runtime, commands, tests, and touched validation/integration code |
| Type checking | Challenge runtime and command modules passed mypy |
| Repository consistency | Navigation/branding, agent manifest, example index, and tracked diff whitespace checks passed |
| Distribution | Source distribution and wheel built using cached dependencies; isolated-network build bootstrap was unavailable, not a source-code failure |
| Installed-package acceptance | All 13 quick-start commands passed from a clean non-editable wheel installation, outside the source-package import path |
| One-command starter acceptance | CLI 0.2.0 base wheel created and verified the portable starter; all 31 internal checks passed; original manifest fingerprint recorded |
| Optional dependencies | Basic workflow passed with cryptography absent; signature round-trip, wrong-key, and tamper tests passed in the signing-enabled test environment |
| Existing suite integration | Evidence manifest accepted the runs/comparison; AISM imported both runs with all 30 cells still unscored |
| Cross-platform CI | Python 3.11/3.12 Linux tests and installed-wheel smoke workflow configured; consult the publication PR checks for their current result |

Skipped locally: a real symlink test requires permissions this Windows host does
not provide, and a real FIFO test requires POSIX. The portable mocked-special-file
test passed; Linux CI must still confirm actual FIFO behavior and link rejection.
No visual browser-session or independent external penetration test is claimed.

Publication-stage artifacts were captured locally under
`.safe2/publication-validation-20260909-1/`: JUnit test results, JSON lint results,
type-check results, the generated starter folder, and AISM/evidence outputs.
These are local review artifacts, not an independent participant study. No
external first-time user acceptance result is claimed. The starter manifest
fingerprint is `9161fe8168e087e1a7ff1296c359f5c1644fee54eb1a73400886dd051e306027`.

## Review findings resolved

- Regrade source state and recompute summaries rather than trusting provider scores.
- Keep shadow-mode vetoes separate from enforced blocking, and preserve unknown
  and incompletely evidenced constrained decisions.
- Retain every original provider episode and verify its normalized translation.
- Distinguish original-byte hashes from canonical-JSON hashes; support checking
  an import against the retained original export.
- Require matching experiment identity, action, and case/trial/treatment coverage
  before reporting outcome agreement; show incomplete and conflicting pairs.
- Correct the quick-start mismatch between 18 all-treatment episodes and the
  six-episode synthetic TENIR reference specimen.
- Preserve safety failures, legitimate-work failures, false blocks, and uncertainty
  in reports instead of presenting a single favorable aggregate score.
- Reject duplicate/non-finite JSON, unsafe file paths, overwrites, and special
  files. Check regular-file status before opening and use nonblocking reads where
  available so a named pipe cannot wait indefinitely for a writer.
- Bind optional signatures to the artifact and signer label, using a caller-trusted
  public key; never treat a signature as upstream factual truth or action approval.
- Escape report data, remove display control characters, and keep HTML free of
  external scripts/assets. Report verification is not permission to execute source content.
- Make AISM ingestion errors readable and prevent output overwrites. Invalid
  Challenge evidence is rejected rather than silently entering an assessment.
- Add a one-command starter and strict folder verification using fixed basenames,
  original-export binding, pinned fixture replay, and regenerated reports. Reject
  resealed fake reports, unsupported versions, duplicate/path-traversal entries,
  extra executable files, and incomplete output directories.

## What the fixture actually showed

These are selected deterministic cases, not measured deployment probabilities.

| Treatment | Unauthorized changes across six cases | Legitimate tasks completed | Legitimate tasks blocked |
|---|---:|---:|---:|
| Uncontrolled | 3 | 3 of 3 | 0 of 3 |
| Conventional fixture ACL | 2 | 3 of 3 | 0 of 3 |
| AI SAFE² reference fixture | 0 | 2 of 3 | 1 of 3 |

The reference fixture's outage hold blocks legitimate work. That utility cost is
part of the result, not a defect to hide. The synthetic TENIR specimen mirrors
the reference cases to test translation; agreement does not provide a second
independent observation or causal evidence that one real product outperforms another.
Approval/replay conditions are fixture inputs, not cryptographic human approvals.

## Applying AI SAFE² to this implementation

The framework guides review questions; this table is candidate alignment, not
a scored assessment of all 161 controls or any regulatory profile.

| Review lens | Evidence in this build | Limit not resolved by fixtures |
|---|---|---|
| Sanitize and isolate | Strict local artifacts, inert state, no provider execution | No hostile live-agent sandbox or verified complete mediation |
| Audit and inventory | Run/source identity, raw records, hashes, manifest integration | External identity and observation authenticity remain unverified |
| Fail-safe and recovery | Unknown/conflict handling, refusal of mismatched comparisons, outage fixture | No live emergency stop, rollback, or descendant revocation validation |
| Engage and monitor | Human Decision Cards expose impacts, gaps, conflicts, and next actions | No ongoing deployment monitoring or calibrated forecasts |
| Evolve and educate | Positive/negative controls, simpler baseline, regression cases, reproducible workflow | No independent operator replication or broad performance benchmark |

## Next stage and remaining limits

1. Obtain a real TENIR export and its documented semantics; verify that the adapter
   preserves meaning. Do not describe the invented example contract as upstream support.
2. Implement the isolated live backend with explicit targets, external stop controls,
   resource caps, and the [Rules of Engagement](../../challenges/001-anthropic-multi-agent-turf-war/ROE.md).
3. Freeze the live protocol, implementation/policy digests, environments, observers,
   and preregistration. Publish failures, bypass tests, and utility costs alongside successes.
4. Commission independent operators before any C5 claim. Neither translation nor
   matching hashes or provider names establishes independence.

Use a trusted local working directory: portable path checks do not defend against
an attacker concurrently replacing parent directories. Source exports may contain
sensitive material and are intentionally preserved, not automatically redacted.
Seals without a trusted signature can be recomputed by an attacker. Even authenticated
artifacts can contain false observations. Confirmatory evidence must satisfy the
full [Challenge evidence requirements](../../challenges/001-anthropic-multi-agent-turf-war/EVIDENCE.md),
not just this offline contract. The candidate package version is 0.2.0; review
the PR and remote CI results before merging or publishing a release.

---

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
