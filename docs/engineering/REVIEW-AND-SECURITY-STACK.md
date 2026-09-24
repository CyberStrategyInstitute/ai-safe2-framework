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
| PR-Agent advisory review | Routine semantic review focused on correctness, security, and regression risk | Advisory; execution failures are visible but do not stop deterministic CI |
| Greptile review status | Confirms whether Greptile substantively reviewed the exact revision | Advisory; missing, stale, or quota-limited reviews are reported without blocking |
| CODEOWNERS and human review | Architecture, authorization, policy, payment, cryptography, data, CI, and release judgment | Required owner approval absent |

PR-Agent is the routine AI reviewer. It is open-source software but still requires a configured model provider and may incur model API cost. Its findings are advisory; deterministic checks and human owners remain authoritative.

Greptile is reserved for major integration points: authentication or authorization, policy and enforcement, payment or settlement, cryptography, evidence integrity, migrations, release candidates, and large cross-boundary changes. `Greptile / Advisory status` distinguishes a substantive current-head review from a quota or error response, but never blocks ordinary development.

## Operating policy

1. Open material changes as draft pull requests after local tests pass.
2. Resolve deterministic failures before requesting semantic review.
3. Use the routine PR-Agent review to find semantic defects; treat failures as visible operational signals, not merge blockers.
4. Request Greptile only at a major integration point, after deterministic checks pass, so credits are spent on stable revisions.
5. Address valid findings, rerun affected first-party checks, and document residual risk.
6. Merge when required deterministic checks and CODEOWNERS approval are current for the tested revision.

## Why the default stack is intentionally smaller

SonarQube is not a default gate because a self-hosted instance adds availability, patching, secret, and administration burdens. Add it only when measured findings show a coverage gap that CodeQL, Semgrep, first-party tests, PR-Agent, and targeted Greptile reviews do not close.

## Repository settings required after merge

Protect `main`; require pull requests, conversation resolution, CODEOWNERS approval, and approval dismissal after new commits. Require the stable job names documented in the table above. Prevent bypass except through a recorded emergency process. Enable Dependabot alerts and security updates, secret scanning/push protection where the GitHub plan allows it, and private vulnerability reporting.
