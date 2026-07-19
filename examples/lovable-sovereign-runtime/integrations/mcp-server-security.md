# Lovable MCP Server Security
## AI SAFE2 v3.0 Integration Guide
**Cyber Strategy Institute**

---

## The Problem With Full-Account Scope

The Lovable MCP server (https://mcp.lovable.dev) authenticates via OAuth.
From the Lovable docs (verified June 2026):

> "Scope is your full account, not one project. Whatever client you connect
> can list, read, and edit every project you have access to in Lovable.
> Calls run live on your account. Tool calls use real credits and edit real projects."

This means:
- An LLM with access to the Lovable MCP token = access to ALL your projects
- `deploy_project` deploys to production immediately
- `query_database` runs as database owner with no RLS filtering
- No per-project scoping is available on the OAuth token

---

## AI SAFE2 Mitigation: Project Allowlist (CP.4)

```python
from enforcement.sovereign_lovable import LovableSovereignRuntime

# Explicitly allowlist which projects an agent may touch
guard = LovableSovereignRuntime(
    allowed_mcp_projects=[
        "proj-dev-sandbox-001",    # dev only
        "proj-staging-abc123",     # staging
        # prod projects NOT listed — require explicit human approval
    ]
)

# Before any MCP tool call that references a project:
guard.scan_mcp_scope(
    scopes=["projects:read", "database:read"],
    project_ids=["proj-dev-sandbox-001"],
    tool_name="query_database",
)
```

---

## MCP Tool Risk Matrix

| Tool | Risk Level | AI SAFE2 Gate |
|---|---|---|
| `get_me` | Low | No gate required |
| `list_workspaces` | Low | No gate required |
| `list_projects` | Low | No gate required |
| `get_project` | Low | Project allowlist check |
| `send_message` | Medium | scan_plan() before approval |
| `get_project_files` | Medium | scan_subagent_file_access() for .env paths |
| `query_database` | **CRITICAL** | scan_sql_query() — ALWAYS |
| `deploy_project` | High | Project allowlist + human HITL |
| `delete_project` | **CRITICAL** | Blocked — requires CP.10 HEAR authority |

---

## Enterprise MCP Disable (Enterprise Workspaces)

From Lovable docs: on Enterprise workspaces, third-party MCP client access
is **disabled by default**. Workspace admin must explicitly enable it via:

> Settings → Privacy & security → Third-party MCP clients

**AI SAFE2 recommendation for Enterprise:** Keep disabled. Enable only for
specific workflows with `allowed_mcp_projects` configured.

---

## Minimal Scope Pattern

Connect the Lovable MCP server with the minimum required scope:

```json
{
  "mcpServers": {
    "lovable-readonly": {
      "type": "http",
      "url": "https://mcp.lovable.dev",
      "comment": "Read-only access — AI SAFE2 governed",
      "note": "Scope: projects:read, database:read only. No write permissions."
    }
  }
}
```

Review Lovable's OAuth scope request before authorizing. If the OAuth
prompt requests write scopes you did not expect, reject and review.
