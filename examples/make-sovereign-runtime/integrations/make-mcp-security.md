# Make MCP Server Security Guide
## AI SAFE2 v3.0 | Cyber Strategy Institute

## Scope Risk Matrix (Verified from developers.make.com, June 2026)

| Scope | Risk Level | Blast Radius | AI SAFE2 Gate |
|---|---|---|---|
| `scenarios:run` | Low | Run specific scenarios | Allowlist check |
| `scenarios:read` | Low | Read all scenarios | Allowlist check |
| `scenarios:write` | **HIGH** | Modify ALL scenarios | Blocked without allowlist |
| `scenarios:delete` | **CRITICAL** | Delete ALL scenarios | Blocked |
| `connections:write` | **HIGH** | Modify all integrations | Blocked |
| `data-stores:write` | **HIGH** | Write all Data Stores | Blocked |
| `teams:write` | **CRITICAL** | Full team management | Always blocked |
| `organizations:write` | **CRITICAL** | Full account takeover | Always blocked |

## Safe MCP Token Pattern

Grant the minimum scope needed. For read-only scenario monitoring:

```
Scope: scenarios:read, scenarios:run
Scenario allowlist: [1001, 1002]   ← only these scenarios callable
```

```python
guard = MakeSovereignRuntime(
    allowed_mcp_scenario_ids=[1001, 1002]
)
guard.scan_mcp_scope(
    ["scenarios:read", "scenarios:run"],
    scenario_ids=[1001, 1002]
)
```

## Scenario Allowlist (CP.4)

The Make MCP Server exposes ALL active scenarios as tools by default.
Use Make's built-in scenario access control + this package's allowlist:

1. In Make: Settings → MCP → Scenario access control → Restrict to specific scenarios
2. In this package: `allowed_mcp_scenario_ids=[1001, 1002]`

Both layers required. This package's allowlist is client-side enforcement.
Make's server-side access control is the authoritative gate.

## Enterprise: Disable Management Scopes

For all production MCP tokens, never grant:
- `teams:write`, `organizations:write`, `users:write`
- These are administrative capabilities, not automation capabilities
- If an LLM needs them, that's a design problem, not a scope to grant
