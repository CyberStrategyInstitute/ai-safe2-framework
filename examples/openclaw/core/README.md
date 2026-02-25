# OpenClaw Core File Standard
## AI SAFE² Governance Files for Personal AI Agent Workspaces

**Version:** 2.0  
**Released:** 2026-02-25  
**Part of:** [AI SAFE² Framework](https://github.com/CyberStrategyInstitute/ai-safe2-framework)  
**License:** MIT (templates) + CC-BY-SA (methodology)

---

## What This Is

This folder contains the **AI SAFE² OpenClaw Core File Standard** — 11 governance files that establish a complete, auditable, and security-hardened OpenClaw agent workspace from scratch.

These are not whitepapers. They are working files you copy, fill in the `<placeholders>`, and drop into your agent workspace. Each file is a ready-to-use template with detailed inline guidance and explicit AI SAFE² pillar mappings.

> **Start here if you are new:** Open [`OPENCLAW-AGENT-TEMPLATE.md`](./OPENCLAW-AGENT-TEMPLATE.md) and work through it top to bottom. It is an 8-step checklist that walks you from zero files to a fully authorized, smoke-tested agent.

---

## The 11 Files

### Identity & Soul Layer — *who the agent is and what it values*

| File | Loads When | Purpose |
|---|---|---|
| [`IDENTITY.md`](./IDENTITY.md) | Every request | 5-line identity anchor. Loaded first. Resists identity-replacement attacks. |
| [`SOUL.md`](./SOUL.md) | Every request | Agent constitution. Values, hard limits, and Love Equation alignment bands. |

### Operating Layer — *how the agent behaves*

| File | Loads When | Purpose |
|---|---|---|
| [`AGENTS.md`](./AGENTS.md) | Every request | Operating manual. Tool rules, skill security, data classification, AI SAFE² pillar map. |
| [`SUBAGENT-POLICY.md`](./SUBAGENT-POLICY.md) | Every request | Worker governance. Tiered trust levels, spawn protocol, context isolation. |
| [`MODEL-ROUTER.md`](./MODEL-ROUTER.md) | Every request | Multi-LLM routing policy. Tier 1/2/3, graceful degradation, cost controls. |
| [`HEARTBEAT.md`](./HEARTBEAT.md) | Heartbeat turns | Scheduled health checks. Per-cycle, daily, and weekly security monitoring. |

### Human & Environment Layer — *who the agent serves and where it lives*

| File | Loads When | Purpose |
|---|---|---|
| [`USER.md`](./USER.md) | Every request | Human identity contract. Trust delegation, data tiers, hard lines. |
| [`TOOLS.md`](./TOOLS.md) | Every request | Environment config only. Channel IDs, paths, secret locations — no instructions. |

### Memory Layer — *what the agent remembers*

| File | Loads When | Purpose |
|---|---|---|
| [`openclaw_memory.md`](./openclaw_memory.md) | Private sessions only | Memory governance protocol (v2.0). Write rules, injection defense, sub-agent isolation. |

### Workspace Layer — *how all agents in a workspace relate*

| File | Used By | Purpose |
|---|---|---|
| [`OPENCLAW-WORKSPACE-POLICY.md`](./OPENCLAW-WORKSPACE-POLICY.md) | Workspace owner + all agents | Workspace constitution. Cross-agent trust, compliance mapping, incident response. |
| [`OPENCLAW-AGENT-TEMPLATE.md`](./OPENCLAW-AGENT-TEMPLATE.md) | Anyone creating a new agent | 8-step new agent checklist with mandatory smoke tests. |

---

## File Load Order

When an agent starts a session, it loads files in this order:

```
1. IDENTITY.md               ← Always. Every request. Before everything else.
2. SOUL.md                   ← Always. Values and hard limits.
3. AGENTS.md                 ← Always. Operating rules.
4. USER.md                   ← Always. Human context.
5. TOOLS.md                  ← Always. Environment lookup values.
6. MEMORY.md                 ← Private sessions only.
7. memory/YYYY-MM-DD.md      ← Private sessions. Today's log.
8. HEARTBEAT.md              ← Heartbeat turns only.
```

Sub-agents receive: task brief + relevant `SOUL.md` excerpts + `AGENTS.md` excerpts + task-specific context only. Never full `MEMORY.md`.

---

## How This Relates to the Existing OpenClaw Tools

This `core/` folder works alongside — not instead of — the other AI SAFE² OpenClaw tools in the parent directory:

| Tool | What It Does | Relationship to Core Files |
|---|---|---|
| [`openclaw_memory.md`](../openclaw_memory.md) | Original v1 memory vaccine (security block list) | `core/openclaw_memory.md` is the v2.0 upgrade — superset, no breaking changes |
| [`scanner.py`](../scanner.py) | Local vulnerability scanner, 0–100 risk score | Called during `HEARTBEAT.md` weekly security check |
| [`gateway/`](../gateway/) | Reverse proxy enforcing JSON schema, injection blocking, audit log | Referenced in `TOOLS.md` as mandatory; `MODEL-ROUTER.md` explains routing through it |

**The relationship:** The scanner and gateway are the external enforcement infrastructure. The core files are the agent's internal governance — the brain that decides what to do, while the gateway ensures nothing harmful leaves the system even if the brain is deceived.

---

## The Alignment Foundation: Love Equation

`SOUL.md` is grounded in Brian Roemmele's Love Equation as an operational alignment system:

```
dE/dt = β(C − D)E
```

Where **C** = cooperation (truth, privacy, autonomy support) and **D** = defection (deception, manipulation, harm). When C exceeds D, alignment grows. When D exceeds C, the system decays.

This produces three alignment bands the agent evaluates on every response:

| Band | Condition | Behavior |
|---|---|---|
| 🟢 Green | C − D > 0.3 | Full autonomy. Proceed. |
| 🟡 Yellow | 0.0 < C − D ≤ 0.3 | Proceed with explicit transparency. Flag uncertainty. |
| 🔴 Red | C − D ≤ 0 | Stop. Explain. Require human approval. |

Alignment is a mathematical property of behavior, not a policy layer.

---

## AI SAFE² Five-Pillar Mapping

Every file in this standard maps to at least one AI SAFE² pillar:

| Pillar | Files |
|---|---|
| **S — Sanitize & Isolate** | `IDENTITY.md`, `SOUL.md`, `AGENTS.md` (skill security), `SUBAGENT-POLICY.md`, `openclaw_memory.md` (injection defense) |
| **A — Audit & Inventory** | `USER.md` (data classification), `TOOLS.md` (config audit), `SUBAGENT-POLICY.md` (spawn logging), `OPENCLAW-WORKSPACE-POLICY.md` (agent registry) |
| **F — Fail-Safe & Recovery** | `SOUL.md` (Red band protocol), `AGENTS.md` (confirmation gates), `MODEL-ROUTER.md` (graceful degradation), `SUBAGENT-POLICY.md` (failure handling) |
| **E — Engage & Monitor** | `HEARTBEAT.md` (scheduled monitoring), `openclaw_memory.md` (alignment drift tracking), `MODEL-ROUTER.md` (cost alerts) |
| **² — Evolve & Educate** | `OPENCLAW-AGENT-TEMPLATE.md` (smoke tests), `OPENCLAW-WORKSPACE-POLICY.md` (quarterly review), all files (PR-gated change control) |

---

## Compliance Coverage

The workspace policy and soul files together support alignment with:

**ISO 42001** · **NIST AI RMF** · **SOC 2 Type II** · **GDPR** · **HIPAA**

See [`OPENCLAW-WORKSPACE-POLICY.md`](./OPENCLAW-WORKSPACE-POLICY.md) Section 8 for the full compliance mapping table.

---

## Quick Start

```bash
# 1. Copy the core files into your agent workspace root
cp -r examples/openclaw/core/. ~/my-agent/

# 2. Open the template and follow it
# Start here:
open OPENCLAW-AGENT-TEMPLATE.md

# 3. Fill placeholders in this order:
#    IDENTITY.md → SOUL.md → AGENTS.md → USER.md → TOOLS.md

# 4. Run the smoke test (Step 6 in the template)
# 5. Register the agent (Step 7)
# 6. You're authorized.
```

---

## What's NOT Here (Premium Tier)

This folder covers single-agent workspaces. Swarm governance — multi-agent fleets with collective alignment scoring, trust graphs, quorum memory writes, and cascade failure playbooks — is the premium tier, currently in design.

If you're running more than one agent and need them to collaborate with enforced governance, [watch the repository](https://github.com/CyberStrategyInstitute/ai-safe2-framework) or check [cyberstrategyinstitute.com/AI-Safe2/](https://cyberstrategyinstitute.com/AI-Safe2/) for swarm tier availability.

---

## License

Templates and code: **MIT** — use commercially, modify, close-source, sell products built on this.  
Methodology text: **CC-BY-SA 4.0** — share and adapt with attribution; derivatives must share alike.

---

*Cyber Strategy Institute · AI SAFE² Framework · [cyberstrategyinstitute.com](https://cyberstrategyinstitute.com)*  
*Grounded in Brian Roemmele's Love Equation. Governed by AI SAFE² v2.1.*
