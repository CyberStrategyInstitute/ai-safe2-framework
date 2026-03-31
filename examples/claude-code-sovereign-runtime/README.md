# Claude Code Sovereign Runtime -- AI SAFE2 Implementation Guide

**Framework:** AI SAFE2 / AISM Level 4 (Sovereign Runtime Governance)

**Source:** Cyber Strategy Institute

**Triggered by:** Claude Code CLI source map leak (March 31, 2026 -- CVE-2026-21852 and prior CVEs)

**Audience:** Individual developers, SMBs, enterprise engineering teams

---

## Why This Exists

On March 31, 2026, the entire TypeScript source of Anthropic's Claude Code CLI was exposed via an accidentally shipped `.js.map` artifact in npm package `@anthropic-ai/claude-code` v2.1.88. Over 512,000 lines of proprietary code -- including every permission gate, bypass mechanism, WebSocket auth structure, and JWT handler -- became publicly reconstructable within hours.

This was not primarily an IP story. It was a **Zero-Day Blueprint Event**: adversaries now have the exact schematic of every guardrail Claude Code implements internally.

The AI SAFE2 conclusion: **you cannot outsource your execution boundary to the vendor's internal software.** The trust boundary must live *outside* the agent, in a Sovereign Runtime Governor you control.

This repo gives you that governor -- for individuals, SMBs, and enterprise teams -- starting in 15 minutes.

---

## Quick Navigation

| I am... | Start here |
|---|---|
| Individual dev who needs immediate protection | [QUICKSTART.md](./QUICKSTART.md) |
| SMB / team lead deploying for a team | [Managed Settings](./managed-settings/) + [Scripts](./scripts/) |
| Enterprise security team | [CI/CD templates](./ci-cd/) + [Monitoring](./monitoring/) + [Managed Settings](./managed-settings/) |
| Using MCP servers / integrations | [Integrations](./integrations/) |
| Looking for the full technical article | [ARTICLE.md](./ARTICLE.md) |

---

## What This Package Implements

### The Five AI SAFE2 Pillars Applied to Claude Code

```
Pillar 1: Sanitize & Isolate    --> hooks/pre-tool-use.sh
Pillar 2: Audit & Inventory     --> scripts/audit-installs.sh + scripts/scan-dangerous-settings.sh
Pillar 3: Fail-Safe & Recovery  --> managed-settings/ + scripts/jit-wrapper.sh
Pillar 4: Engage & Monitor      --> monitoring/ + hooks/post-tool-use.sh
Pillar 5: Evolve & Educate      --> ARTICLE.md + tabletop scenarios in docs/
```

### Controls Implemented

| Control | File | Risk Addressed |
|---|---|---|
| Deny `--dangerously-skip-permissions` | `managed-settings/*.json` | Exposed bypass logic (YOLO mode) |
| Block dangerous bash patterns | `hooks/pre-tool-use.sh` | Prompt injection, supply chain worms |
| Subprocess env scrubbing | `hooks/pre-tool-use.sh` | Credential exfiltration |
| JIT credential wrapping | `scripts/jit-wrapper.sh` | Long-lived key exposure (CVE-2026-21852) |
| Settings file audit | `scripts/scan-dangerous-settings.sh` | Overly broad permissions |
| Installation inventory | `scripts/audit-installs.sh` | Unknown attack surface |
| Output monitoring | `hooks/post-tool-use.sh` | Secret leakage (3.2% baseline) |
| Session cleanup | `hooks/stop.sh` | Credential persistence |
| Safe CI/CD templates | `ci-cd/` | Pipeline exposure |
| MCP server proxy/validation | `integrations/mcp-proxy.sh` | Adversarial MCP servers |
| Hardened CLAUDE.md | `CLAUDE.md` | Jailbreak / manipulation |

---

## The Architectural Principle

```
WITHOUT this framework:
  User Intent --> Claude Code (vendor TypeScript guardrails) --> Your Infrastructure
                                    ^
                                    | Guardrails now publicly readable
                                    | Adversary can bypass with leaked source

WITH this framework:
  User Intent --> [External Pre-Hook: YOUR CONTROLS] --> Claude Code --> [External Post-Hook] --> Your Infrastructure
                        ^                                                        ^
                        | Enforced at OS/network layer                          | Monitored externally
                        | Agent code cannot see or influence these              | Agent cannot suppress logs
```

The Sovereign Runtime Governor does not ask Claude to reconsider. It enforces at the syscall or network layer. An adversary who perfectly bypasses Claude Code's internal guardrails using the leaked source still hits your wall -- because your wall is not in Claude Code's code.

---

## Critical CVEs This Addresses

| CVE | Issue | This Package |
|---|---|---|
| CVE-2026-21852 | Pre-trust API requests leak Anthropic API keys | JIT wrapper + key rotation script |
| CVE-2025-64755 | sed parsing bypass --> arbitrary file write | Pre-tool-use hook pattern matching |
| CVE-2025-58764 | Command parsing bypasses approval prompts | Pre-tool-use hook + managed deny list |
| CVE-2025-59828 | Yarn config execution before trust dialog | Startup hook + managed settings |
| CVE-2025-52882 | WebSocket from arbitrary origins | Managed settings + network policy |

---

## Compatibility

| Deployment Type | Supported |
|---|---|
| Claude Code CLI (standalone) | Yes |
| Claude Code in VS Code extension | Yes |
| Claude Code in Cursor | Yes |
| Claude Code in GitHub Actions | Yes (see ci-cd/) |
| Claude Code in GitLab CI | Yes (see ci-cd/) |
| Claude Code with MCP servers | Yes (see integrations/) |
| Claude Code in devcontainers | Yes (see ci-cd/) |
| Claude Code in cloud workstations | Yes (see managed-settings/) |
| Claude Code Enterprise (Team/Enterprise plans) | Yes -- enhanced controls available |

---

## Version Requirements

- Claude Code >= 1.0.0 (hooks system available)
- bash >= 4.0 (hooks)
- Node.js >= 18 (monitoring scripts)
- Optional: jq (recommended for hook JSON parsing)

---

## License

MIT. Use freely. Fork it. Improve it. The threat is real and moving fast.

---

## Contributing

Found a bypass? New CVE? Better hook pattern? Open a PR. This is a living document and the threat model is evolving daily.

---

*Cyber Strategy Institute -- AI SAFE2 Framework*
*Last updated: March 31, 2026*
