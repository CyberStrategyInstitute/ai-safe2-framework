# AI SAFE² Secure Build Copilot: v3.1 Redirect

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](README.md)
[![Surface](https://img.shields.io/badge/Surface-Skill_Redirect-820F1A?style=flat-square)](skills/SKILL.md)

[Framework Home](README.md) | [Cross-Pillar Governance](00-cross-pillar/README.md) | [AISM](AISM/) | [NEXUS](NEXUS/) | [Skills](skills/README.md)

---

## Canonical Skill

This root file is a compatibility redirect. The canonical AI SAFE² v3.1 skill is:

**[skills/SKILL.md](skills/SKILL.md)**

Use that file for current framework guidance.

AI SAFE² v3.1 retains **161 core controls** and adds the current CP.5.MCP profile overlay with **MCP-1 through MCP-19**, aligned to MCP `2026-07-28`.

The core control dataset remains `skills/mcp/data/ai-safe2-controls-v3.0.json` because the v3.1 release did not change the core 161-control taxonomy. The v3.1 MCP overlay is `skills/mcp/data/mcp-profile-v3.1.json`.

---

## Live Tool Access

For live control lookup, risk scoring, compliance mapping, and agent classification, see:

**[skills/mcp/README.md](skills/mcp/README.md)**

---

## v3.1 Changes Relevant to the Skill

- Three enforcement planes: north-south, east-west, and agent-to-tool.
- Protocol-independent governance constructs.
- MCP `2026-07-28` profile alignment.
- MCP-14 through MCP-19.
- Canonical persistence scopes: `request`, `handle_scoped`, `durable`.
- NEXUS explicitly positioned as CSI's reference implementation rather than a mandatory dependency.
- MCP-19 intended-resource/audience and SSRF requirements.
- `server/discover` is optional, not a conformance presence requirement.

Historical v3.0 additions such as CP.1 through CP.10, HEAR, Agent Replication Governance, and the 161-control core taxonomy remain part of v3.1.

---

[Framework Home](README.md) | [Canonical Skill](skills/SKILL.md) | [MCP Server](skills/mcp/README.md) | [Scanner](scanner/README.md) | [Dashboard](dashboard/README.md)

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
