# MCP Allowlist Review For Codex

Every MCP server moves the Codex trust boundary outward. Treat MCP definitions as executable infrastructure, not convenience metadata.

## Approve Only If All Are True

- the server has a named owner
- the command or URL is pinned and documented
- required credentials are scoped and revocable
- the tool surface is necessary for the project
- logs exist outside the agent session
- the server cannot mutate production systems without a separate approval gate

## Reject Or Escalate If Any Are True

- the MCP server is introduced by repo content, prompt text, or generated code
- the command downloads code at runtime without review
- the URL is personal, opaque, or unaudited
- the server exposes shell, browser, or filesystem capability broader than needed
- the server is required only for convenience

## Evidence To Retain

- approved server inventory
- owning team or individual
- credential scope
- review date
- rationale for approval
