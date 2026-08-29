# AI SAFE² v3.1 MCP Server

> 161 framework controls. 32 mapped frameworks. CP.5.MCP profile aligned to MCP `2026-07-28`.

[![Version](https://img.shields.io/badge/AI_SAFE2-v3.1.0-orange)](https://cyberstrategyinstitute.com/ai-safe2/)
[![Framework Controls](https://img.shields.io/badge/Framework_Controls-161-blue)]()
[![MCP Profile](https://img.shields.io/badge/CP.5.MCP-19_controls-blue)]()
[![MCP Spec](https://img.shields.io/badge/MCP-2026--07--28-blue)]()
[![Frameworks](https://img.shields.io/badge/Frameworks-32-blue)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey)]()

---

## What This Is

The AI SAFE² MCP server exposes the framework taxonomy and MCP security profile to MCP-compatible clients such as Claude Code, Codex, Cursor, and other agent runtimes.

AI SAFE² v3.1 separates two counts deliberately:

- **161 framework controls:** the five pillars plus the Cross-Pillar Governance Layer.
- **19 CP.5.MCP profile controls:** MCP-specific requirements under CP.5. These are profile controls and are not added to the 161 framework total.

The server loads the stable 161-control core taxonomy and overlays the v3.1 MCP profile so MCP-1 through MCP-19 are directly queryable.

## v3.1 Security Model

AI SAFE² v3.1 is aligned to MCP `2026-07-28` and does not use protocol-owned session state as the governance identity or authorization boundary.

Governance instead binds to:

- verified principals;
- capability grants;
- delegation chains;
- provenance baselines;
- trust-establishment events;
- principal-scoped state handles;
- policy decisions and audit evidence.

The governing CP.5 rule is:

> A CP.5 profile MUST NOT bind a control to a construct owned by the protocol it profiles.

`server/discover` is optional in MCP `2026-07-28` and is not required for AI SAFE² conformance.

## Three Enforcement Planes

| Plane | Traffic | Primary concern |
|---|---|---|
| North-south | Agent to model provider | Content, policy, consumption, spend |
| East-west | Agent to agent | Identity, delegation, lineage, authority |
| Agent-to-tool | Agent to MCP server or tool | Tool authorization, provenance, output trust, economic amplification |

The MCP server primarily serves the **agent-to-tool** plane.

## CP.5.MCP Profile

The current MCP profile contains 19 controls:

| Range | Coverage |
|---|---|
| MCP-1 through MCP-13 | Core server/tool hardening, trust, audit, state, provenance, delegation, and revocation |
| MCP-14 | Extension capability negotiation |
| MCP-15 | Header/body assertion integrity |
| MCP-16 | State-handle binding and lifecycle |
| MCP-17 | MRTR round-trip integrity and replay resistance |
| MCP-18 | Catalog-cache integrity and provenance revalidation |
| MCP-19 | Authorization-chain integrity, intended resource/audience validation, and SSRF boundaries |

Canonical profile: [`../../00-cross-pillar/cp5_mcp_server_security.md`](../../00-cross-pillar/cp5_mcp_server_security.md)

Machine-readable profile: [`data/mcp-profile-v3.1.json`](data/mcp-profile-v3.1.json)

## MCP-19 and Authentication

Legacy static bearer tokens remain supported for entitlement compatibility, but an opaque token does not contain an audience claim. Static-token possession therefore does **not** by itself demonstrate MCP-19 audience-validation conformance.

A deployment claiming MCP-19 must validate the intended resource or audience, or establish equivalent resource binding with independently reconstructable evidence.

Use `MCP_AUTH_AUDIENCE` for deployments that add JWT/OAuth audience validation.

## Quick Start

### Local stdio

Local stdio runs without a remote bearer token and is scoped to the local process boundary.

```bash
cd skills/mcp
pip install -e .
MCP_TRANSPORT=stdio python -m mcp_server.app
```

Example Claude Code configuration:

```json
{
  "mcpServers": {
    "ai-safe2": {
      "command": "python",
      "args": ["-m", "mcp_server.app"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "PYTHONPATH": "/absolute/path/to/ai-safe2-framework/skills/mcp/src"
      }
    }
  }
}
```

Example Codex configuration:

```toml
[mcp_servers.ai-safe2-local]
command = "python"
args = ["-m", "mcp_server.app"]
env = { MCP_TRANSPORT = "stdio", PYTHONPATH = "/absolute/path/to/ai-safe2-framework/skills/mcp/src" }
```

### Remote streamable HTTP

For remote deployment, terminate TLS in front of the service and configure authentication appropriate to the environment.

```text
MCP_TRANSPORT=streamable-http
MCP_HOST=127.0.0.1
MCP_PORT=8000
TOKENS=legacy_token:free
MCP_AUTH_AUDIENCE=https://mcp.example.com/
```

Treat `TOKENS` as a legacy entitlement mechanism. Do not describe it as MCP-19-complete authorization.

## What the Server Provides

The server supports framework-oriented capabilities including:

- control lookup;
- compliance mapping;
- risk scoring;
- code review;
- agent classification;
- framework resources;
- MCP profile lookup through the controls database.

`ControlsDB.count()` keeps framework and profile counts separate to prevent accidental claims that the framework has 180 controls.

## NEXUS Relationship

AI SAFE² specifies what must be governed and enforced. NEXUS is Cyber Strategy Institute's first-party reference implementation for agent-to-agent and agent-to-tool enforcement.

Organizations may use NEXUS or another implementation that demonstrably satisfies the applicable AI SAFE² controls and required evidence.

The v3.1 NEXUS MCP adapter is currently a fail-closed interface contract. Unimplemented methods raise rather than silently allowing traffic. It should not be represented as production-ready until the enforcement implementation is connected and tested.

See [`../../NEXUS/adapters/mcp/`](../../NEXUS/adapters/mcp/).

## Compatibility

MCP `2025-11-25` is retained as a legacy compatibility binding for twelve months after the v3.1 release. Legacy `Mcp-Session-Id` values are treated only as principal-scoped state handles, not identity or authorization boundaries.

## Data Model

The MCP server intentionally uses a layered data model:

```text
data/ai-safe2-controls-v3.0.json  -> stable 161-control core taxonomy
data/mcp-profile-v3.1.json       -> CP.5.MCP 19-control protocol profile
```

The release version is v3.1 even though the unchanged core taxonomy source remains v3.0. This prevents duplicated control databases and makes profile-level expansion explicit.

## Testing Expectations

Before a v3.1 release or MCP security change is considered complete, verify at minimum:

- the server loads the core taxonomy and v3.1 MCP profile;
- `MCP-14` through `MCP-19` resolve through the controls database;
- the framework total remains 161;
- the profile total is 19;
- optional `server/discover` is not required;
- incomplete enforcement remains fail-closed;
- authorization tests include wrong-resource/wrong-audience cases;
- red-team coverage includes header/body desynchronization, state-handle guessing, MRTR replay, cache staleness, OAuth mix-up, and localhost/endpoint identity confusion.

---

AI SAFE² v3.1, Cyber Strategy Institute
