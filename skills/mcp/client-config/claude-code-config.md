# Connecting Claude Code to the AI SAFE2 MCP Server

## Option A: Local stdio (Recommended for developers)
No token needed. No network. Inherently secure.

Add to your Claude Code `settings.json`:
```json
{
  "mcpServers": {
    "ai-safe2": {
      "command": "python",
      "args": ["-m", "mcp_server.app"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "PYTHONPATH": "/path/to/ai-safe2-framework/skills/mcp/src"
      }
    }
  }
}
```

Or using Docker:
```json
{
  "mcpServers": {
    "ai-safe2": {
      "command": "docker",
      "args": ["run", "--rm", "-i",
               "-e", "MCP_TRANSPORT=stdio",
               "ai-safe2-mcp"]
    }
  }
}
```

## Option B: Remote HTTPS endpoint (Pro token required)

Add to your Claude Code `settings.json`:
```json
{
  "mcpServers": {
    "ai-safe2": {
      "url": "https://your-domain.example/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_HERE"
      }
    }
  }
}
```

Replace `YOUR_TOKEN_HERE` with your token from:
https://cyberstrategyinstitute.com/ai-safe2/

## Available Tools

Once connected, Claude Code has access to:

| Tool | Description | Tier |
|------|-------------|------|
| `lookup_control` | Search 161 AI SAFE2 controls | Free (30 results) / Pro (all) |
| `risk_score` | Calculate Combined Risk Score with AAF | Free (basic) / Pro (full AAF) |
| `compliance_map` | Map requirements to controls across 32 frameworks | Free (5 FW) / Pro (all 32) |
| `code_review` | Review code against SAFE2 controls | Pro only |
| `agent_classify` | Classify agent ACT tier + governance requirements | Pro full |
| `get_governance_resource` | Policy templates, checklists, schemas | Free (3) / Pro (all) |
| `get_workflow_prompt` | Reusable workflow prompts | All tiers |

## Quick Test

After connecting, ask Claude:
> "Use the AI SAFE2 MCP server to look up the HEAR Doctrine control (CP.10)"

Expected: Claude returns the full CP.10 control with HEAR requirements, Class-H action protocol, and compliance mappings.
