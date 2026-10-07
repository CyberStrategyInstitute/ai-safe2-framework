<!-- AI-SAFE2-UX:START -->
[![AI SAFE² v3.1](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../../README.md)
[![Surface: Example](https://img.shields.io/badge/Surface-Example-820F1A?style=flat-square)](../README.md)
[![Context: v3.1 Current](https://img.shields.io/badge/Context-v3.1_Current-808080?style=flat-square)](../../docs/REPOSITORY-UX-STANDARD.md)

[Framework Home](../../README.md) | [Examples Index](../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [AISM](../../AISM/) | [NEXUS](../../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

> **Current framework context:** AI SAFE² v3.1. This example may preserve historical component versions or earlier framework references where they describe when the implementation was created. For current conformance, use the v3.1 framework and applicable profile requirements.
<!-- AI-SAFE2-UX:END -->

<!-- stack: MCP (protocol security) -->
<!-- description: Moved. Use safe2 scan mcp, safe2 score mcp, safe2 gate mcp and safe2 mcp wrap-stdio / wrap-proxy (CP.5.MCP v3.1). -->

# MCP Security Toolkit: moved into the `safe2` CLI

The `mcp-score`, `mcp-scan` and `mcp-safe-wrap` code that used to live here was a
pre-migration copy. It now ships as `aisafe2_mcp_tools` inside the `ai-safe2`
package and is reached through `safe2`. The copy in this folder was removed on
2026-10-07 because it still contained the remote scorer that could be gamed by
self-attestation (fixed in the packaged toolkit) and cited retired v3.0 control
numbers. Do not install from this path.

| You want to | Run |
|---|---|
| Score a remote MCP server | `safe2 score mcp https://server.example/mcp` |
| Statically scan MCP server source | `safe2 scan mcp ./server` |
| Fail CI below a score or on hostile tool content | `safe2 gate mcp https://server.example/mcp --ci-fail-below 70` |
| Wrap a stdio server with inspection, policy and audit | `safe2 mcp wrap-stdio -- <server command>` |
| Wrap an HTTP server | `safe2 mcp wrap-proxy https://server.example/mcp` |

The legacy entry points `mcp-score`, `mcp-scan` and `mcp-safe-wrap` are still
installed by `pip install ai-safe2`. Findings and checks cite the
[CP.5.MCP v3.1 profile](../../00-cross-pillar/cp5_mcp_server_security.md)
(MCP-1 to MCP-19). See the [command map](../../safe2/README.md#command-map) and
[MIGRATION.md](../../MIGRATION.md) for the move.

<!-- AI-SAFE2-UX-FOOTER:START -->
---

### Repository navigation

[Examples Index](../README.md) | [Framework Home](../../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [NEXUS](../../NEXUS/) | [Scanner](../../scanner/README.md) | [MCP Profile](../../00-cross-pillar/cp5_mcp_server_security.md)

*AI SAFE² v3.1 | Cyber Strategy Institute*
<!-- AI-SAFE2-UX-FOOTER:END -->
