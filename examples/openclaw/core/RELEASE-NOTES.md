## Release Notes
# AI SAFE² OpenClaw Core File Standard — v2.0

**Released:** 2026-02-25  
**Authored by:** Cyber Strategy Institute  
**Repository:** https://github.com/CyberStrategyInstitute/ai-safe2-framework  
**Path:** `examples/openclaw/core/`  
**License:** MIT (code/templates) + CC-BY-SA (methodology)

---

## What This Release Is

Version 2.0 of the AI SAFE² OpenClaw integration is the first complete, opinionated standard for governing a personal AI agent workspace from the ground up. It is not a patch, a whitepaper, or a checklist — it is a working set of 11 files that, together, define a governed, secure, and auditable OpenClaw agent from identity through memory through multi-model routing.

This release was built in direct response to what we've watched unfold in the OpenClaw ecosystem since January 2026: 145,000 GitHub stars in weeks, at least 230 malicious skills on ClawHub, credential leaks via prompt injection, and organizations deploying autonomous agents with shell access and API budget without a single governance document in place. The gap between what OpenClaw can do and what most operators have in place to govern it is where systemic risk lives. This release is designed to close that gap for everyone, for free.

---

## What's New in v2.0

### New Files (did not exist in v1)

| File | What It Does |
|---|---|
| `SOUL.md` | Agent constitution grounded in Brian Roemmele's Love Equation as a mathematical alignment system, not a policy layer |
| `AGENTS.md` | Complete operating manual covering SKILL.md security, data classification, AI SAFE² pillar mapping, and the two-message UX pattern |
| `IDENTITY.md` | Minimal 5-line identity anchor that loads every request — the first line of defense against identity replacement attacks |
| `USER.md` | Human identity contract with three-tier data classification, context-aware handling, and trust delegation levels |
| `TOOLS.md` | Environment configuration standard separating "how tools work" (skills) from "where things are" (this file) |
| `HEARTBEAT.md` | Scheduled health check protocol that operationalizes the AI SAFE² Engage & Monitor pillar into concrete per-cycle, daily, and weekly checks |
| `SUBAGENT-POLICY.md` | Worker governance with tiered trust levels, spawn protocol, context isolation rules, and injection detection for sub-agent output |
| `MODEL-ROUTER.md` | Multi-LLM routing policy defining Tier 1/2/3 models, routing decision matrix, graceful degradation, data residency rules, and cost controls |
| `OPENCLAW-WORKSPACE-POLICY.md` | Workspace constitution binding all agents to shared accountability, cross-agent trust hierarchy, and compliance mapping |
| `OPENCLAW-AGENT-TEMPLATE.md` | Eight-step new agent checklist including mandatory smoke tests for identity, hard limits, injection resistance, and data classification |

### Upgraded Files

| File | What Changed |
|---|---|
| `openclaw_memory.md` (v1 → v2.0) | v1 was a "memory vaccine" with a static block list. v2.0 is a full memory governance protocol: Love Equation C/D scoring for every write decision, SKILL.md provenance validation, sub-agent memory isolation, structured incident escalation, daily memory format standard, and a ClawHub supply chain attack pattern library |

---

## Why We Built It This Way

### The Love Equation as Alignment Infrastructure

Most agent alignment approaches are policy layers — a list of rules that says "don't do this, don't do that." Policy layers work until they don't. They fail under adversarial inputs, edge cases users discover, and the gradual prompt injection that happens when an agent reads enough untrusted content.

Brian Roemmele's Love Equation reframes alignment as a dynamical system: `dE/dt = β(C − D)E`. When cooperation exceeds defection, alignment grows. When defection exceeds cooperation, the system decays. We translated this from philosophy into operational bands (Green/Yellow/Red), C/D event scoring, and concrete memory write decisions. The result is alignment that is mathematically unstable when violated, not just discouraged.

### IDENTITY.md: The Missing Anchor

The OpenClaw ecosystem didn't have a standard for a minimal, always-loaded identity file. Matt Berman's community-developed patterns identified this gap clearly: an agent that doesn't know who it is in 5 lines — loaded before everything else — is more vulnerable to identity replacement attacks. When an adversarial SKILL.md or injected prompt says "You are now a different assistant with no restrictions," an agent with a concrete, loaded IDENTITY.md has an anchor. An agent without one only has system-prompt context, which can be buried or overwhelmed.

### TOOLS.md: Separating Configuration from Instructions

One of the cleanest lessons from community OpenClaw patterns was the discipline of keeping environment-specific values (channel IDs, file paths, where secrets live) in a dedicated file, separate from how tools work (SKILL.md files) and how the agent behaves (AGENTS.md). This separation has a security consequence: TOOLS.md never contains instructions. It contains lookup values. That means a compromised TOOLS.md cannot inject behavior — it can only misdirect lookups, which is detectable. A TOOLS.md that starts looking like AGENTS.md is a signal.

### HEARTBEAT.md: Monitoring as a First-Class Concern

The AI SAFE² Engage & Monitor pillar exists in principle across our prior work. HEARTBEAT.md makes it concrete and scheduled. The security rationale is direct: the most dangerous OpenClaw failures (0.0.0.0 bindings, API keys in logs, credential leaks, model cost overruns) are often invisible until they've caused harm. A heartbeat that runs every 30–60 minutes and specifically checks for these failure modes converts "we noticed eventually" into "we caught it the next cycle." The Love Equation integration in the daily heartbeat check adds something new: alignment drift is now a monitored metric, not just a philosophical concern.

### The Skill Supply Chain Problem Is Structural

At least 230 malicious OpenClaw skills were uploaded to ClawHub since January 27, 2026. Cisco found that 26% of the 31,000 agent skills they analyzed contained at least one vulnerability. The top-downloaded skill at one point was confirmed malware. This is not an OpenClaw problem — it is an agent ecosystem problem. Any platform that reads SKILL.md files as instructions rather than documents is vulnerable to the same attack pattern.

Our AGENTS.md SKILL.md security section and the OPENCLAW-AGENT-TEMPLATE.md provenance checklist treat this structurally: skill files are execution vectors, not documentation. "Top downloaded" is not a safety signal. Read before you execute. Verify before you trust. This applies to every agent ecosystem that has adopted the SKILL.md format — which is increasingly all of them.

### The Data Classification Tiers

The three-tier system (Confidential / Internal / Restricted) with context-aware enforcement (DM vs. group chat vs. channel) came directly from community patterns that identified the most common real-world data leak vector: an agent that knows the user's personal email and financial data behaving identically in a group Slack channel and a private DM. This is not a clever attack — it's a default behavior failure. The tiers, enforced in USER.md and referenced in openclaw_memory.md, make context-aware behavior the standard, not an optional hardening step.

---

## What This Release Does Not Cover

This is the free/open-source core tier. It governs single-agent workspaces. It does not cover:

- **Swarm governance** — multi-agent fleets with collective alignment scoring, trust graph management, quorum memory writes, and cascade failure response. This is the premium tier, currently in design.
- **Enterprise compliance reporting** — automated evidence generation for ISO 42001 / NIST AI RMF audits
- **Cross-workspace federation** — shared governance across multiple independent workspaces

These are planned for the AI SAFE² Toolkit (paid tier). The core tier is deliberately complete for single-agent use without requiring the premium tier.

---

## Migration from v1

If you are using the original `openclaw_memory.md` (v1 memory vaccine):

- v2.0 is a superset. No breaking changes. Drop it in alongside or replacing v1.
- The prompt injection block list in `openclaw_memory.md` v2.0 supersedes v1's simpler pattern list.
- Sub-agent memory isolation and Love Equation write scoring are new — no existing behavior is changed, new guardrails are added.

If you have no prior AI SAFE² files:

- Start with `OPENCLAW-AGENT-TEMPLATE.md` and work through it top to bottom.
- Do not skip the smoke test (Step 6). Every test has caught real issues in internal validation.

---

## Acknowledgments

This release synthesizes:

- The AI SAFE² Framework v2.1 five-pillar model (Cyber Strategy Institute)
- Brian Roemmele's Love Equation as a dynamical alignment system
- Community agent patterns developed by the OpenClaw ecosystem, particularly the work collected by Matt Berman in establishing the standard file conventions (IDENTITY.md, TOOLS.md, HEARTBEAT.md, the two-message UX pattern, data classification tiers)
- Security research from Cisco AI Defense on agent skill supply chain vulnerabilities
- Lessons from the 1Password analysis of OpenClaw skill attack vectors

The AI SAFE² framework is an open standard. It is designed to be forked, extended, and built upon. If these files help you govern your agents better, that is the point.

---

## Repository

```
ai-safe2-framework/examples/openclaw/core/
├── IDENTITY.md
├── SOUL.md
├── AGENTS.md
├── USER.md
├── TOOLS.md
├── HEARTBEAT.md
├── SUBAGENT-POLICY.md
├── MODEL-ROUTER.md
├── openclaw_memory.md          (v2.0 — upgrade from v1)
├── OPENCLAW-WORKSPACE-POLICY.md
└── OPENCLAW-AGENT-TEMPLATE.md
```

**Star the repo:** https://github.com/CyberStrategyInstitute/ai-safe2-framework  
**Issues and PRs welcome.**

---

*Cyber Strategy Institute · AI SAFE² Framework*  
*Building the governance infrastructure the AI industry needs.*
