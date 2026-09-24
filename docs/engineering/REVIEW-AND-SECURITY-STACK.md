# Review and Security Stack

This repository uses layered evidence. No single scanner or reviewer is treated as proof of safety.

## Required pull-request gates

| Gate | Purpose | Blocking condition |
| --- | --- | --- |
| Existing CI and repository consistency checks | Behavior, compatibility, packaging, and framework invariants | Any required job fails |
| Gitleaks | Credential and secret exposure across Git history | Any finding not present in the reviewed, fully redacted fixture baseline |
| Repository-owned Semgrep rules | High-confidence dangerous implementation patterns | Any matching rule |
| Python dependency audit | Known vulnerabilities on shipped Python dependency surfaces | Any unignored published advisory |
| Dependency review | Newly introduced vulnerable dependencies | High or critical severity |
| CodeQL | Cross-file code security analysis | Branch rule and code-scanning policy determine blocking severity |
| Greptile current-head gate | Independent semantic review of the exact proposed revision | Missing, stale, quota-limited, degraded, or non-substantive review |
| CODEOWNERS and human review | Architecture, authorization, policy, payment, cryptography, data, CI, and release judgment | Required owner approval absent |

Greptile is the final corroborating review, not a substitute for deterministic checks or a decision authority. A bot comment is not sufficient: `Greptile / Current-head review` verifies a substantive review event for the current head SHA and rejects quota/error messages.

## Operating policy

1. Open material changes as draft pull requests after local tests pass.
2. Resolve deterministic failures before requesting semantic review.
3. Mark ready for review to trigger the final Greptile wait gate.
4. Address valid findings, rerun affected first-party checks, and document residual risk.
5. Merge only when required checks and CODEOWNERS approval are current for the tested revision.

## Why the default stack is intentionally smaller

PR-Agent and SonarQube are not default gates. PR-Agent substantially overlaps Greptile, while a self-hosted SonarQube instance adds availability, patching, secret, and administration burdens. Add either only when measured findings show a coverage gap that CodeQL, Semgrep, first-party tests, and Greptile do not close.

## Repository settings required after merge

Protect `main`; require pull requests, conversation resolution, CODEOWNERS approval, and approval dismissal after new commits. Require the stable job names documented in the table above. Prevent bypass except through a recorded emergency process. Enable Dependabot alerts and security updates, secret scanning/push protection where the GitHub plan allows it, and private vulnerability reporting.
