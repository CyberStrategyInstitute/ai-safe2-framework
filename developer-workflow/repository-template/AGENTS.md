# AI SAFE2 repository instructions

Read `.ai-safe2/workflow.json` and the active product profile before changing
the repository.

- Preserve the developer's requested outcome and identify affected trust
  boundaries.
- Use an isolated branch or worktree for material changes.
- Add or update tests in proportion to the change.
- Do not treat a provider outage, silence, malformed response, or successful
  wrapper job as a completed review.
- Record the exact revision, commands, results, limitations, and unresolved
  risks.
- For CI failures, inspect and record environment preflight, build, transport,
  test, post-processing, and evidence-publication phases separately. A generic
  wrapper exit code is not a root cause.
- Preserve discovered, executed, passed, failed, and skipped test counts. A
  passing test phase followed by a wrapper or publication failure is failed CI
  evidence, not an application assertion failure and not produced evidence.
- Keep multiline CI orchestration in a repository-owned, syntax-tested script
  unless the action's execution contract explicitly preserves one shell.
- Do not merge, release, deploy, change policy, access unrelated secrets, or
  accept residual risk unless the human explicitly authorizes that action.
- Claude, Codex, and other providers are interchangeable evidence producers.
  Do not modify another provider's configuration unless the user asks.
- When explaining this installation, generate or refresh
  `AI-SAFE2-DEVELOPER-WORKFLOW.md` with `scripts/explain_workflow.py`. Describe
  the before/after process, active routes, optional modules, limitations, and
  next choices. Do not imply that a listed provider is connected or ran.


## v3.5 adoption context

Resolve the current root framework manifest, child-clause catalog and `docs/data/v35-ecosystem-adoption.json` in the reviewed framework checkout. If this template is installed elsewhere, record the pinned source revision and missing context. Component versions and publication are separate from framework status. For consequential changes, identify the exact target/environment, delegated scope, consumption limits, side-effect ledger, success criteria, independent observer and recovery owner. Do not turn a plan, receipt, model review or source fixture into execution authority or production conformance.
