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

1. The preflight queries OpenRouter's model catalog and per-model endpoint metadata.
   It filters an eight-model, review-capable pool for zero price, sufficient context,
   unexpired availability, endpoint status, and at least 75% recent uptime.
2. It ranks the live routes by five-minute uptime, then 30-minute and daily uptime,
   and sends the same compact request only to the top three. This lets temporary
   high-quality routes such as `stealth/space-bunny-alpha` participate until their
   published expiration, while low-health routes are excluded automatically.
   Degraded status is retained as evidence but does not suppress a route that still
   clears the uptime floor; the canary provides the final availability proof.
3. A candidate must return valid concise JSON, find both known canary defects at
   the correct location, and avoid findings on the verified-safe control. The
   highest score wins; response length and latency break ties.
4. The same request includes up to 12,000 characters from one risk-prioritized hunk
   in the actual PR to confirm context and moderate-input compatibility. Its
   speculative findings do not increase the score because that would reward
   hallucination when the hunk is correct.
5. `gpt-5.6-luna` through the official OpenAI API is the final, metered fallback
   when no free candidate passes or the selected model produces no review.

The chain uses exact model IDs. `openrouter/free` is deliberately excluded because
its randomly selected model prevents dependable replay and before/after comparison.
Inkling is also excluded from this text-diff path: its multimodal advantage is not
needed for routine pull-request review and would add another provider data boundary.
Model selection is a dated policy snapshot, not a permanent ranking; change it only
through retained evaluation evidence and an explicit configuration review.

This policy was recalibrated on October 1, 2026. On PR #370, Laguna S 2.1 entered
generation but produced no publication before the ten-minute job limit. The current
OpenRouter catalog placed Qwen 3.8 27B ahead of Laguna S on latency. A subsequent
Qwen attempt received the full diff and the configured 75-second timeout but still
held the provider call until the job limit, so PR-Agent's internal fallback never
ran. The workflow therefore enforces failover outside PR-Agent: GitHub hard-stops
the selected free attempt after three minutes, checks for a substantive publication,
and invokes one OpenAI attempt for at most five minutes only when needed. A later
Laguna run passed the small canary but stalled after PR-Agent sent the entire
58.5K-token diff. The free route is therefore capped at 16K tokens to produce a
bounded, risk-focused review instead of treating small-call availability as proof
of full-diff throughput. The metered fallback retains a 64K budget. Receipts retain
both budgets, route outcomes, and whether metered fallback ran.

The selector deliberately canary-tests three models rather than every free model.
Catalog and endpoint-health calls do not invoke a model; they cheaply narrow the
curated pool before inference quota is spent. Testing every free model before every
PR would consume the daily allowance without improving decision quality
proportionally. Three canary calls plus one real review allow up to roughly 12
complete PR attempts within a 50-request day. The claim is therefore "best passing
model in the live, review-capable shortlist," never "globally best free model."

The canary is versioned and includes two real defects plus a safe control. Rotate
or expand the vetted fixtures through an evidence-backed policy change when the
benchmark stops discriminating between candidates. Sol-low and Astra-low are
independent design baselines, not OpenRouter candidates and not recurring calls.

Baseline run on October 1, 2026:

| Independent baseline | Reasoning | Defects | Safe false positives | JSON | Score |
| --- | --- | ---: | ---: | --- | ---: |
| `gpt-6-sol` | low | 2/2 | 0 | valid | 100/100 |
| `gpt-6-astra` | low | 2/2 | 0 | valid | 100/100 |

Both baselines located authorization-after-read and path traversal at `C2` and
left the safe control unflagged. These results validate the canary shape; they do
not place either model in the free OpenRouter ranking.

OpenRouter uses the repository `OPENROUTER_API_KEY` secret and OpenAI uses
`OPENAI_KEY`. Same-model retries are disabled so a transient provider failure moves
to the next bounded option instead of consuming the free request allowance. Run
details and provider-reported cost are enabled so reviewer availability, selected
model, and consumption can be assessed together. OpenRouter's free plan is limited
to 50 requests per day and has no availability guarantee. Prove one representative
review before launching a multi-PR batch, then stage the batch to preserve quota.
GitHub Models is not used because GitHub retired that service on July 30, 2026.
Each retained execution receipt records the eligible catalog count, curated pool,
endpoint uptime/status evidence, dynamic top-three shortlist, per-model
latency/failure/score evidence, selected model, prompt and patch hashes, provider
outcomes, and the model observed in a substantive publication. Raw credentials and
raw model responses are not retained.

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
