# AI SAFE2 v3.0 Skills Ecosystem

This folder contains the complete AI SAFE2 v3.0 skill and MCP server implementation.
It supersedes the root `skill.md` (v2.1) and is the canonical reference for all
AI model integrations.

---

## What's Here

```
skills/
├── SKILL.md                    ← Claude Projects: upload this to Project Knowledge
├── skill-spec.md               ← Model-neutral canonical behavior specification
├── evals.md                    ← Regression tests and expected output patterns
├── chatgpt/gpt-instructions.md ← ChatGPT Custom GPT instructions
├── gemini/gem-instructions.md  ← Gemini Gem instructions
├── perplexity/system-instructions.md ← Perplexity / other LLM system prompt
└── mcp/                        ← MCP server (Python, Docker, Railway-ready)
    ├── README.md               ← Setup and deploy guide
    ├── src/mcp_server/         ← Server source code
    ├── data/ai-safe2-controls-v3.0.json ← 161-control taxonomy (the backbone)
    ├── Dockerfile
    ├── docker-compose.yml      ← With Caddy sidecar for automatic HTTPS
    └── tests/
```

---

## Quick Start by Use Case

### "I use Claude Projects / Claude Desktop"
Upload `SKILL.md` to your Claude Project's knowledge base. Done.
Your Claude instance is now an AI SAFE2 v3.0 architect.

### "I want live control lookup in Claude Code / Codex"
See `mcp/README.md` for stdio local setup (5 minutes, no token needed).

### "I want a shared HTTPS endpoint for my team"
See `mcp/README.md` for Railway deployment (15 minutes, free tier available).
Issue tokens at cyberstrategyinstitute.com/ai-safe2/

### "I use ChatGPT"
Use `chatgpt/gpt-instructions.md` as the GPT system instructions.
Attach `mcp/data/ai-safe2-controls-v3.0.json` as a knowledge file.

### "I use Gemini"
Use `gemini/gem-instructions.md` as the Gem instructions.
Attach `SKILL.md` and `mcp/data/ai-safe2-controls-v3.0.json` as files.

---

## What the MCP Server Provides

| Tool | Description | Free | Pro |
|------|-------------|------|-----|
| `lookup_control` | Search 161 controls by keyword, ID, pillar, framework | 30 results | 500 results |
| `risk_score` | CVSS + Pillar + AAF combined risk formula | Basic | Full AAF |
| `compliance_map` | Map requirements to controls across 32 frameworks | 5 frameworks | All 32 |
| `code_review` | Review code against controls (light, model-based) | No | Yes |
| `agent_classify` | ACT tier + HEAR + CP.9 + governance evidence | Partial | Full |
| `get_governance_resource` | Policy templates, checklists, schemas | 3 resources | All |
| `get_workflow_prompt` | Reusable workflow starters | Yes | Yes |

**Tokens:** cyberstrategyinstitute.com/ai-safe2/
Free tier: email registration. Pro tier: Toolkit purchase ($97).

---

## Framework Version

| | v2.1 | v3.0 |
|---|---|---|
| Controls | 128 pillar | 151 pillar + 10 CP = **161 total** |
| Frameworks | 14 | **32** |
| First-in-field | — | CP.9 Replication, CP.10 HEAR, CP.7 Active Defense, AIVSS AAF |
| Skill location | root skill.md | **skills/SKILL.md** (this folder) |

---

*Managed by [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
