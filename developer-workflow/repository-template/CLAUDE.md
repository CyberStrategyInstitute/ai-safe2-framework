# Claude project guidance

Follow `AGENTS.md`, `.ai-safe2/workflow.json`, and the active product profile.
Claude may plan, implement, test, or review, but its output is advisory evidence
until a named human decides to merge or release.

Do not change Codex configuration, model selection, hooks, MCP servers, or
credentials. If another provider reviewed the same revision, retain both
attributed results and identify disagreements rather than overwriting either.

When the user asks what this workflow changed, generate or refresh
`AI-SAFE2-DEVELOPER-WORKFLOW.md` with `scripts/explain_workflow.py` and explain
the active routes, options, boundaries, and next choices. A provider named in
configuration is not evidence that it is connected or ran.

