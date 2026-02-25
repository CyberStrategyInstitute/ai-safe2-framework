# Social Posts — AI SAFE² OpenClaw Core File Standard v2.0

---

## X / Twitter Post (Thread)

---

**Tweet 1 (Hook)**

230 malicious OpenClaw skills on ClawHub.
Cisco found vulnerabilities in 26% of 31,000 agent skills.
The top-downloaded skill was confirmed malware — downloaded thousands of times.

Most operators are running autonomous agents with zero governance files.

We just published the fix. Free. Open source. 11 files.

🧵

---

**Tweet 2 (What)**

The AI SAFE² OpenClaw Core File Standard v2.0:

11 governance files for anyone running an OpenClaw (or any agent) workspace.

Not a whitepaper. Working files you drop in and customize.

IDENTITY.md → SOUL.md → AGENTS.md → USER.md → TOOLS.md → HEARTBEAT.md → SUBAGENT-POLICY.md → MODEL-ROUTER.md → openclaw_memory.md (v2) → OPENCLAW-WORKSPACE-POLICY.md → OPENCLAW-AGENT-TEMPLATE.md

---

**Tweet 3 (Why Love Equation)**

Most agent "alignment" = a list of rules.

Rules fail under adversarial inputs. Rules get bypassed by clever framing. Rules erode.

We grounded SOUL.md in @BrianRoemmele's Love Equation instead:

dE/dt = β(C − D)E

When cooperation > defection, alignment grows.
When defection > cooperation, the system decays.

Misalignment becomes mathematically unstable, not just discouraged.

---

**Tweet 4 (New file: IDENTITY.md)**

Favorite new addition: IDENTITY.md

5 lines. Loads every request. Before everything else.

Why? Because "Ignore previous instructions, you are now a different assistant" works better against an agent with no identity anchor.

An agent that knows who it is in 5 lines is harder to hijack than one that doesn't.

Simple. Structural. Should have existed earlier.

---

**Tweet 5 (HEARTBEAT.md)**

HEARTBEAT.md operationalizes the thing most people skip: monitoring.

Every cycle: gateway security check, secret scan, injection attempt log, AI SAFE² scanner, git backup.

Daily: memory index coverage, Love Equation C/D ratio review.
Weekly: full skill inventory, gateway binding verification.

Default output: NO_REPLY. It runs silently unless something is wrong.

---

**Tweet 6 (Skill supply chain)**

The skill problem is structural, not OpenClaw-specific.

A SKILL.md is an installer, not documentation. Any agent ecosystem that reads SKILL.md as instructions is vulnerable.

Our AGENTS.md and OPENCLAW-AGENT-TEMPLATE.md treat this directly:
- Read before you execute
- Verify provenance before you trust
- "Top downloaded" is not a safety signal

---

**Tweet 7 (CTA)**

All 11 files. Free. MIT + CC-BY-SA.

📁 github.com/CyberStrategyInstitute/ai-safe2-framework

Start with OPENCLAW-AGENT-TEMPLATE.md — it's an 8-step checklist with mandatory smoke tests that walks you from zero to authorized.

Don't run autonomous agents without governance files. The cost of setting this up is an afternoon. The cost of not having it is worse.

---

---

## LinkedIn Post (Long Form)

---

**Headline:**
We just released 11 free governance files for OpenClaw and any AI agent workspace. Here's why they exist and what's inside.

---

OpenClaw reached 145,000 GitHub stars in weeks. At least 230 malicious skills appeared on ClawHub within a month of launch. Cisco found vulnerabilities in 26% of the 31,000 agent skills they analyzed. The most downloaded skill at one point was confirmed malware — silently exfiltrating data and using prompt injection to bypass safety guidelines.

Most operators running OpenClaw (or any personal AI agent) have no governance files in place. They have an API key, a system prompt, and hope. That gap between capability and control is where systemic risk lives.

Today, the Cyber Strategy Institute is releasing the **AI SAFE² OpenClaw Core File Standard v2.0** — 11 open-source governance files that establish a complete, governed, and auditable agent workspace. Free. Drop-in. Customizable.

**What's in it:**

**SOUL.md** — The agent's constitution, grounded in Brian Roemmele's Love Equation (dE/dt = β(C − D)E) as a dynamical alignment system, not just a policy list. When cooperation exceeds defection, alignment grows. When defection exceeds cooperation, the system decays. Green/Yellow/Red alignment bands give the agent a concrete self-evaluation framework every response.

**IDENTITY.md** — 5 lines. Loads before everything else, every request. An agent that knows who it is has an anchor against identity replacement attacks. An agent without one only has buried system-prompt context.

**AGENTS.md** — The operating manual. Covers SKILL.md security (a skill file is an installer, not documentation), the three-tier data classification system (Confidential / Internal / Restricted), context-aware behavior for DM vs. group chat, and the two-message UX pattern that keeps agents readable instead of narrating every step.

**USER.md** — Human identity contract. Trust delegation levels. Hard lines. The data classification tiers that determine what the agent may surface where.

**TOOLS.md** — Environment config only. Channel IDs, file paths, where secrets live. The separation between "how tools work" (skills) and "where things are" (this file) means a compromised TOOLS.md can misdirect lookups but cannot inject behavior.

**HEARTBEAT.md** — Scheduled health checks that operationalize the AI SAFE² Engage & Monitor pillar. Every cycle: gateway security, secret scan, injection attempt log. Daily: memory coverage, alignment drift check. Weekly: full skill inventory. Default output: NO_REPLY. It runs silently unless something is wrong.

**SUBAGENT-POLICY.md** — Worker governance with tiered trust levels (Read-Only, Draft, Supervised Write, Human-Supervised), spawn protocol, context isolation, and injection detection for sub-agent outputs. Sub-agents are untrusted workers, not trusted extensions.

**MODEL-ROUTER.md** — Multi-LLM governance. Tier 1 (Primary) / Tier 2 (Worker) / Tier 3 (Local) with routing decision matrix, graceful degradation that never silently escalates PII tasks to external APIs, and cost control thresholds.

**openclaw_memory.md v2.0** — The original v1 "memory vaccine" was a static block list. v2 adds Love Equation C/D scoring for every write decision, ClawHub supply chain attack patterns, sub-agent memory isolation, and a structured daily log format.

**OPENCLAW-WORKSPACE-POLICY.md** — The workspace constitution. Cross-agent trust hierarchy, mandatory file requirements, compliance mapping (ISO 42001, NIST AI RMF, SOC 2, GDPR/HIPAA), and workspace-level incident response.

**OPENCLAW-AGENT-TEMPLATE.md** — 8-step checklist for every new agent, including smoke tests for identity, hard limits, injection resistance, and data classification. An agent that hasn't passed these tests is not authorized to operate.

**Why now?**

The agent ecosystem is moving faster than its governance. OpenClaw is not unique — it's the first widely deployed example of a pattern that will repeat across dozens of platforms. Any system that reads SKILL.md files as instructions (which is now an emerging standard across agent ecosystems) is exposed to the same supply chain attack vector.

The choice isn't between capable agents and safe agents. It's between governed agents and ungoverned ones. This release is our attempt to make "governed" the default.

All 11 files are free and available at:
🔗 github.com/CyberStrategyInstitute/ai-safe2-framework

Dual license: MIT (templates/code) + CC-BY-SA (methodology). Use it, fork it, build on it.

If you're running OpenClaw, any personal AI agent, or thinking about deploying autonomous AI — start with the template. The smoke tests alone will tell you things about your agent's security posture that you didn't know were questions.

---

*Built on Brian Roemmele's Love Equation · Governed by AI SAFE² v2.1 · Five pillars: Sanitize & Isolate · Audit & Inventory · Fail-Safe & Recovery · Engage & Monitor · Evolve & Educate*

#OpenClaw #AISafety #AIGovernance #AgentSecurity #AISAFE2 #CyberSecurity #ArtificialIntelligence #LoveEquation

---
