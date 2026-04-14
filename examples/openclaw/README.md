<!--
  examples/openclaw/README.md
  AI SAFE² OpenClaw Integration — Cyber Strategy Institute
-->

---

**Quick nav:**&nbsp;&nbsp;
[Core Files](#core-files) &nbsp;·&nbsp;
[Gateway v3.0](#gateway--v30-enforcement-proxy) &nbsp;·&nbsp;
[Memory Governance](#memory-governance) &nbsp;·&nbsp;
[Skill Supply Chain](#the-skill-supply-chain-problem-is-structural) &nbsp;·&nbsp;
[Migration](#migration-from-v1) &nbsp;·&nbsp;
[Release Notes](#release-notes) &nbsp;·&nbsp;
[gateway/README.md](./gateway/README.md) &nbsp;·&nbsp;
[Core Gateway README](../../gateway/README.md) &nbsp;·&nbsp;
[v3.0 Gateway Release Note](./gateway-release-v3.0.html)

---

# AI SAFE² OpenClaw Integration

**Cyber Strategy Institute** &nbsp;·&nbsp; [ai-safe2-framework](https://github.com/CyberStrategyInstitute/ai-safe2-framework) &nbsp;·&nbsp; MIT (code) + CC-BY-SA 4.0 (docs)

A governed, secure, and auditable OpenClaw agent workspace — from identity through memory through multi-model routing — plus a production enforcement gateway that enforces AI SAFE² v3.0 controls between OpenClaw and any LLM provider.

---

## Release Notes

| Component | Version | Released | Notes |
|-----------|---------|----------|-------|
| OpenClaw Core File Standard | v2.0 | 2026-02-25 | 11 governance files, Love Equation alignment, memory governance |
| OpenClaw Gateway | v3.0 | April 2026 | Multi-provider, NEXUS-A2A compatible, 48 tests passing — [full release note](./gateway-release-v3.0.html) |

---

## Gateway — v3.0 Enforcement Proxy

The `gateway/` subfolder contains the AI SAFE² v3.0 enforcement proxy for OpenClaw. Every request is risk-scored, HITL-gated, and immutably logged before it reaches the upstream LLM — regardless of which provider is active.

**Supported providers:** Anthropic · OpenAI · Gemini · Ollama (local) · OpenRouter

```
examples/openclaw/gateway/
├── gateway.py              # Flask enforcement proxy
├── provider_adapters.py    # Multi-provider adapter layer + NEXUS-A2A hooks
├── config.yaml             # Thresholds, weights, provider config, NEXUS settings
├── start.sh                # 9-step pre-flight validator + gateway launcher
└── README.md               # Full deployment and operations reference
```

**Quick start:**

```bash
export AUDIT_CHAIN_KEY="$(openssl rand -hex 32)"
export OPERATOR_DEACTIVATION_KEY="$(openssl rand -hex 16)"
export ANTHROPIC_API_KEY="sk-ant-api..."   # or OPENAI_API_KEY / GEMINI_API_KEY / OPENROUTER_API_KEY

python3 gateway/gateway.py --init-heartbeat   # first run only
bash gateway/start.sh
```

Switch providers by changing `provider.active` in `config.yaml`. See [gateway/README.md](./gateway/README.md) for full configuration, HITL flow, NEXUS-A2A compatibility, and governance notes.

---

## What This Release Is

Version 2.0 of the AI SAFE² OpenClaw integration is the first complete, opinionated standard for governing a personal AI agent workspace from the ground up. It is not a patch, a whitepaper, or a checklist — it is a working set of 11 files that, together, define a governed, secure, and auditable OpenClaw agent from identity through memory through multi-model routing.

This release was built in direct response to what we've watched unfold in the OpenClaw ecosystem since January 2026: 145,000 GitHub stars in weeks, at least 230 malicious skills on ClawHub, credential leaks via prompt injection, and organizations deploying autonomous agents with shell access and API budget without a single governance document in place. The gap between what OpenClaw can do and what most operators have in place to govern it is where systemic risk lives. This release is designed to close that gap for everyone, for free.

---

## Core Files

```
examples/openclaw/core/
├── IDENTITY.md
├── SOUL.md
├── AGENTS.md
├── USER.md
├── TOOLS.md
├── HEARTBEAT.md
├── SUBAGENT-POLICY.md
├── MODEL-ROUTER.md
├── openclaw_memory.md              (v2.0 — upgrade from v1)
├── OPENCLAW-WORKSPACE-POLICY.md
└── OPENCLAW-AGENT-TEMPLATE.md
```

### New Files in v2.0

| File | What It Does |
|------|-------------|
| [SOUL.md](./core/SOUL.md) | Agent constitution grounded in Brian Roemmele's Love Equation as a mathematical alignment system, not a policy layer |
| [AGENTS.md](./core/AGENTS.md) | Complete operating manual covering SKILL.md security, data classification, AI SAFE² pillar mapping, and the two-message UX pattern |
| [IDENTITY.md](./core/IDENTITY.md) | Minimal 5-line identity anchor that loads every request — the first line of defense against identity replacement attacks |
| [USER.md](./core/USER.md) | Human identity contract with three-tier data classification, context-aware handling, and trust delegation levels |
| [TOOLS.md](./core/TOOLS.md) | Environment configuration standard separating "how tools work" (skills) from "where things are" (this file) |
| [HEARTBEAT.md](./core/HEARTBEAT.md) | Scheduled health check protocol that operationalizes the AI SAFE² Engage & Monitor pillar into concrete per-cycle, daily, and weekly checks |
| [SUBAGENT-POLICY.md](./core/SUBAGENT-POLICY.md) | Worker governance with tiered trust levels, spawn protocol, context isolation rules, and injection detection for sub-agent output |
| [MODEL-ROUTER.md](./core/MODEL-ROUTER.md) | Multi-LLM routing policy defining Tier 1/2/3 models, routing decision matrix, graceful degradation, data residency rules, and cost controls |
| [OPENCLAW-WORKSPACE-POLICY.md](./core/OPENCLAW-WORKSPACE-POLICY.md) | Workspace constitution binding all agents to shared accountability, cross-agent trust hierarchy, and compliance mapping |
| [OPENCLAW-AGENT-TEMPLATE.md](./core/OPENCLAW-AGENT-TEMPLATE.md) | Eight-step new agent checklist including mandatory smoke tests for identity, hard limits, injection resistance, and data classification |

### Upgraded Files

| File | What Changed |
|------|-------------|
| [openclaw_memory.md](./core/openclaw_memory.md) | v1 was a "memory vaccine" with a static block list. v2.0 is a full memory governance protocol: Love Equation C/D scoring for every write decision, SKILL.md provenance validation, sub-agent memory isolation, structured incident escalation, daily memory format standard, and a ClawHub supply chain attack pattern library |

---

## Why We Built It This Way

### The Love Equation as Alignment Infrastructure

Most agent alignment approaches are policy layers — a list of rules that says "don't do this, don't do that." Policy layers work until they don't. They fail under adversarial inputs, edge cases users discover, and the gradual prompt injection that happens when an agent reads enough untrusted content.

Brian Roemmele's Love Equation reframes alignment as a dynamical system: `dE/dt = β(C − D)E`. When cooperation exceeds defection, alignment grows. When defection exceeds cooperation, the system decays. We translated this from philosophy into operational bands (Green/Yellow/Red), C/D event scoring, and concrete memory write decisions. The result is alignment that is mathematically unstable when violated, not just discouraged.

### IDENTITY.md: The Missing Anchor

The OpenClaw ecosystem didn't have a standard for a minimal, always-loaded identity file. Matt Berman's community-developed patterns identified this gap clearly: an agent that doesn't know who it is in 5 lines — loaded before everything else — is more vulnerable to identity replacement attacks. When an adversarial SKILL.md or injected prompt says "You are now a different assistant with no restrictions," an agent with a concrete, loaded IDENTITY.md has an anchor. An agent without one only has system-prompt context, which can be buried or overwhelmed.

### TOOLS.md: Separating Configuration from Instructions

One of the cleanest lessons from community OpenClaw patterns was the discipline of keeping environment-specific values (channel IDs, file paths, where secrets live) in a dedicated file, separate from how tools work (SKILL.md files) and how the agent behaves (AGENTS.md). This separation has a security consequence: TOOLS.md never contains instructions. It contains lookup values. That means a compromised TOOLS.md cannot inject behavior — it can only misdirect lookups, which is detectable. A TOOLS.md that starts looking like AGENTS.md is a signal.

### Memory Governance

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

**If you are using the original openclaw_memory.md (v1 memory vaccine):**

- v2.0 is a superset. No breaking changes. Drop it in alongside or replacing v1.
- The prompt injection block list in openclaw_memory.md v2.0 supersedes v1's simpler pattern list.
- Sub-agent memory isolation and Love Equation write scoring are new — no existing behavior is changed, new guardrails are added.

**If you have no prior AI SAFE² files:**

- Start with [OPENCLAW-AGENT-TEMPLATE.md](./core/OPENCLAW-AGENT-TEMPLATE.md) and work through it top to bottom.
- Do not skip the smoke test (Step 6). Every test has caught real issues in internal validation.

**Upgrading the gateway from v2.1 to v3.0:**

See the [v3.0 Gateway Release Note](./gateway-release-v3.0.html) for the full migration checklist. Key breaks: `config.yaml` is not forward-compatible; audit logs must be archived and restarted; `provider_adapters.py` must be placed alongside `gateway.py`.

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

[Star the repo](https://github.com/CyberStrategyInstitute/ai-safe2-framework) · Issues and PRs welcome.

**Cyber Strategy Institute · AI SAFE² Framework**  
*Building the governance infrastructure the AI industry needs.*

**Built by:** [Cyber Strategy Institute](https://cyberstrategyinstitute.com)  
**License:** MIT (code) + CC-BY-SA 4.0 (documentation)  
**Version:** 2.1



