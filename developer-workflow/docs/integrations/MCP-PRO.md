# MCP Pro integration

MCP Pro is the professional execution-boundary surface for Claude Code, Cursor,
Codex, and other supported development tools. It should consume AI SAFE2 Core
contracts and return normalized evidence rather than becoming a second policy
engine.

The adapter may expose classification, risk scoring, framework mapping, and
implementation review according to the deployed product entitlement. The
workflow must not infer paid capability from documentation alone.

Integration requirements:

- authenticate without placing tokens in repository files;
- record endpoint, adapter version, capability used, and subject revision;
- validate the response against the evidence schema;
- distinguish entitlement denial, timeout, malformed output, and completed
  review;
- publish only sanitized summaries;
- never treat MCP availability as authorization to merge or release.

Public reference: https://cyberstrategyinstitute.com/ai-safe2/mcp/

