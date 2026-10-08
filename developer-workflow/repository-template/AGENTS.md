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
- Do not merge, release, deploy, change policy, access unrelated secrets, or
  accept residual risk unless the human explicitly authorizes that action.
- Claude, Codex, and other providers are interchangeable evidence producers.
  Do not modify another provider's configuration unless the user asks.

