# AI SAFE² Skills Ecosystem
### Model-facing framework guidance and live MCP control access

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Surface](https://img.shields.io/badge/Surface-Skills-820F1A?style=flat-square)](./README.md)
[![Core](https://img.shields.io/badge/Core-161_controls-808080?style=flat-square)](./mcp/data/ai-safe2-controls-v3.0.json)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

## What This Folder Does

The `skills/` surface packages AI SAFE² guidance for AI assistants and provides the Python MCP server used for live control lookup and governance workflows.

The current v3.1 data model separates the stable core taxonomy from the protocol profile overlay:

```text
skills/mcp/data/ai-safe2-controls-v3.0.json  161-control core taxonomy
skills/mcp/data/mcp-profile-v3.1.json       CP.5.MCP profile, MCP-1 through MCP-19
```

The v3.0 filename on the core taxonomy is intentional historical provenance. AI SAFE² v3.1 did not add new core controls; it updated the MCP profile and enforcement model.

---

## Repository Map

```text
skills/
├── README.md
├── SKILL.md                         Canonical framework skill
├── skill-spec.md                    Model-neutral behavior specification
├── evals.md                         Regression/evaluation expectations
├── chatgpt/gpt-instructions.md      ChatGPT-facing instructions
├── gemini/gem-instructions.md       Gemini-facing instructions
├── perplexity/system-instructions.md
└── mcp/
    ├── README.md                    MCP server setup and architecture
    ├── src/mcp_server/              Server implementation
    ├── data/
    │   ├── ai-safe2-controls-v3.0.json
    │   └── mcp-profile-v3.1.json
    └── tests/
```

---

## Quick Start by Use Case

### AI project or knowledge context

Use [`SKILL.md`](./SKILL.md) as the primary framework context and follow the target product's supported method for project or system instructions.

### Live control lookup and MCP workflows

Use the [AI SAFE² MCP Server](./mcp/README.md). It exposes core-control lookup plus the separate v3.1 MCP profile.

### ChatGPT-facing instructions

Use [`chatgpt/gpt-instructions.md`](./chatgpt/gpt-instructions.md) and provide the core taxonomy/profile artifacts required for the use case.

### Gemini-facing instructions

Use [`gemini/gem-instructions.md`](./gemini/gem-instructions.md) together with the relevant framework data artifacts.

---

## MCP Server Capabilities

| Capability | Purpose |
|---|---|
| `lookup_control` | Search the 161 core controls and v3.1 MCP profile controls by ID or text |
| `risk_score` | Apply the AI SAFE² combined risk model |
| `compliance_map` | Reuse control evidence across mapped frameworks |
| `code_review` | Review implementation patterns against applicable controls |
| `agent_classify` | Estimate ACT tier and surface governance requirements |
| governance resources | Retrieve policy, schema, and workflow guidance |

See [skills/mcp/README.md](./mcp/README.md) for current transport, authentication, compatibility, and MCP-19 limitations.

---

## v3.1 Version Model

| Item | v3.1 state |
|---|---|
| Core framework controls | **161** |
| Core Cross-Pillar controls | **CP.1 through CP.10** |
| MCP profile controls | **MCP-1 through MCP-19** |
| Current MCP binding | **2026-07-28** |
| Legacy MCP binding | **2025-11-25, migration compatibility** |
| Canonical skill | **skills/SKILL.md** |
| NEXUS role | **CSI reference implementation, not mandatory dependency** |

UAS is a 27-requirement regulatory profile extension, not CP.11, and does not add new controls to the 161-control core.

---

## Conformance Boundary

Skills and MCP tools help users interpret and operationalize AI SAFE². They do not create conformance merely by being installed.

A conformant implementation must satisfy the applicable control outcomes and produce the required evidence. For MCP, this includes the v3.1 profile requirements relevant to the deployment, including authorization/resource binding when MCP-19 applies.

---

## 🔗 Navigation

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [MCP Server](./mcp/README.md) | [Scanner](../scanner/README.md) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
