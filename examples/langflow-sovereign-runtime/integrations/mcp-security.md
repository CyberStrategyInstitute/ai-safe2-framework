# Langflow MCP Server Security
## AI SAFE2 v3.0 | Cyber Strategy Institute

## The Default-On Risk

From docs.langflow.org/mcp-server (verified June 2026):

> "When you create a Langflow project, Langflow automatically adds the
> project to your MCP server's configuration and makes the project's
> flows available as MCP tools."

The environment variable to change this:
`LANGFLOW_ADD_PROJECTS_TO_MCP_SERVERS` — defaults to **True**.

## Required Configuration Before Enabling MCP

```bash
# .env — REQUIRED before any MCP exposure

# 1. Disable auto-add (LF-MCP control)
LANGFLOW_ADD_PROJECTS_TO_MCP_SERVERS=false

# 2. Enable authentication (required for MCP API key generation)
LANGFLOW_AUTO_LOGIN=false
LANGFLOW_SUPERUSER=admin@yourorg.com
LANGFLOW_SUPERUSER_PASSWORD=your-strong-password

# 3. Selectively enable MCP per project via Langflow UI:
#    Project → Share → MCP Server → Edit Tools → select specific flows
```

## Scope Risk Matrix

| Scope | Risk | Mitigation |
|---|---|---|
| All flows auto-exposed | CRITICAL | Set LANGFLOW_ADD_PROJECTS_TO_MCP_SERVERS=false |
| AUTO_LOGIN=true + MCP enabled | CRITICAL | Set LANGFLOW_AUTO_LOGIN=false |
| No per-project allowlist | HIGH | Configure allowed_mcp_project_ids in runtime |
| Flow tool names = flow UUIDs | MEDIUM | Set descriptive names per MCP docs |

## Safe MCP Pattern

```python
guard = LangflowSovereignRuntime(
    allowed_mcp_project_ids=["proj-safe-001", "proj-safe-002"],
    auto_login_allowed=False,  # enforce authentication
)

# Validate on startup:
guard.scan_mcp_config(
    auto_expose_enabled=False,  # LANGFLOW_ADD_PROJECTS_TO_MCP_SERVERS=false
    exposed_project_ids=["proj-safe-001"]  # only explicitly configured projects
)
```
