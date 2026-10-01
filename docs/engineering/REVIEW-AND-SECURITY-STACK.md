# Review and Security Stack

This repository uses layered evidence. No single scanner or reviewer is treated as proof of safety.

See [PR Decision-Evidence Workflow](./PR-DECISION-EVIDENCE-WORKFLOW.md) for the
complete architecture, authority boundaries, diagrams, before/after comparison,
provider strategy, tradeoffs, and reviewer procedure.

## Required pull-request gates

| Gate | Purpose | Blocking condition |
| --- | --- | --- |
| Existing CI and repository consistency checks | Behavior, compatibility, packaging, and framework invariants | Any required job fails |
| Gitleaks | Credential and secret exposure across Git history | Any finding not present in the reviewed, fully redacted fixture baseline |
| Repository-owned Semgrep rules | High-confidence dangerous implementation patterns | Any matching rule |
| Python dependency audit | Known vulnerabilities on shipped Python dependency surfaces | Any unignored published advisory |
| Dependency review | Newly introduced vulnerable dependencies | High or critical severity |
| CodeQL | Cross-file code security analysis | Branch rule and code-scanning policy determine blocking severity |
| PR-Agent advisory availability | Routine semantic review focused on correctness, security, and regression risk | A substantive publication is verified after every attempt; absence fails this advisory check but it is not a required merge check |
| Greptile review status | Confirms whether Greptile substantively reviewed the exact revision | Advisory; missing, stale, or quota-limited reviews are reported without blocking |
| CODEOWNERS and human review | Architecture, authorization, policy, payment, cryptography, data, CI, and release judgment | Required owner approval absent |
| AI SAFE2 decision evidence | Exact base/head risk classification, CLI 0.9.0 environment drift, required evidence, and machine/human records | Evidence generation fails; risk itself routes review rather than automatically blocking |

PR-Agent is the routine AI reviewer. Its software is open source. The provider
chain deliberately prefers free inference, while keeping provider failure visible:

1. `openrouter/qwen/qwen3.8-27b:free` is the pinned primary. It combines coding
   specialization, structured-output support, 262K context, and the lowest current
   catalog latency among the retained review routes.
2. `gpt-5.6-luna` through the official OpenAI API is the final, metered fallback.
   It is chosen over Terra for cost-sensitive routine review.

The chain uses exact model IDs. `openrouter/free` is deliberately excluded because
its randomly selected model prevents dependable replay and before/after comparison.
Inkling is also excluded from this text-diff path: its multimodal advantage is not
needed for routine pull-request review and would add another provider data boundary.
Model selection is a dated policy snapshot, not a permanent ranking; change it only
through retained evaluation evidence and an explicit configuration review.

This order was recalibrated on October 1, 2026. On PR #370, Laguna S 2.1 entered
generation but produced no publication before the ten-minute job limit. The current
OpenRouter catalog placed Qwen 3.8 27B ahead of Laguna S on latency. A subsequent
Qwen attempt received the full diff and the configured 75-second timeout but still
held the provider call until the job limit, so PR-Agent's internal fallback never
ran. The workflow therefore enforces failover outside PR-Agent: GitHub hard-stops
one free Qwen attempt after three minutes, checks for a substantive publication,
and invokes one OpenAI attempt for at most five minutes only when needed. A 64K
context budget lets the measured 47.3K-token change use one call instead of pruned
chunks. Receipts retain both route outcomes and whether metered fallback ran.

North Mini Code and Nemotron Ultra remain useful evaluation candidates, but they
are not automatic fallbacks. A long-lived upstream call cannot reach an in-process
fallback, and serial runner-enforced attempts against several free providers would
add latency and consume quota before the known metered recovery route.

OpenRouter uses the repository `OPENROUTER_API_KEY` secret and OpenAI uses
`OPENAI_KEY`. Same-model retries are disabled so a transient provider failure moves
to the next bounded option instead of consuming the free request allowance. Run
details and provider-reported cost are enabled so reviewer availability, selected
model, and consumption can be assessed together. OpenRouter's free plan is limited
to 50 requests per day and has no availability guarantee. Prove one representative
review before launching a multi-PR batch, then stage the batch to preserve quota.
GitHub Models is not used because GitHub retired that service on July 30, 2026.
Each retained execution receipt records the ordered provider policy and the model
observed in the substantive review publication, allowing provider failover and
model-policy changes to be separated from code-quality changes in longitudinal
comparisons.

This free route is approved only for this repository's public pull-request content.
Do not copy it to a private or sensitive repository unless the applicable model
provider's retention/training terms and OpenRouter privacy controls have been
reviewed and enforced. A free endpoint is not evidence that data handling is safe.

PR-Agent findings remain advisory; deterministic checks and human owners remain
authoritative. The workflow does not equate an action exit code with review
completion: it verifies that a current-attempt bot publication contains substantive
output, writes a privacy-minimized JSON execution receipt, and reports
`review_unavailable` when the provider emits a failure message or no review. This
advisory availability check is intentionally excluded from the required-status
ruleset.

Greptile is reserved for major integration points: authentication or authorization, policy and enforcement, payment or settlement, cryptography, evidence integrity, migrations, release candidates, and large cross-boundary changes. `Greptile / Advisory status` distinguishes a substantive current-head review from a quota or error response, but never blocks ordinary development.

`Review Decision Evidence` applies `.ai-safe2/review-policy.json` to the exact
base/head diff, runs the released AI SAFE2 CLI 0.9.0 against comparable baseline
and current checkouts, and retains JSON, Markdown, and hashes for 90 days. The
report intentionally records unavailable historic finding attribution as unknown.
It never converts absence of prior structured evidence into zero inherited defects.

Release builds retain the same decision record and artifact hashes for 365 days.
This makes each release comparable going forward. The first retained run is the
baseline; direct before/after claims begin only when two comparable records exist.

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

Configure `OPENROUTER_API_KEY` as an Actions repository secret. The OpenRouter key
requires only inference access; do not use a management key. Keep `OPENAI_KEY` as
the final fallback credential. Missing, exhausted, or rejected credentials must
remain visible as `review_unavailable`, never as approval. Because the selected
free endpoints may retain or use inputs and outputs to improve their services, this
route is restricted to already-public pull-request material and must not receive
secrets, unpublished vulnerability details, personal data, or private source code.
