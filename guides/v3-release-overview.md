# AI SAFE² v3.0 — Complete Features, Benefits & Advantages Reference

**Cyber Strategy Institute | April 2026**
**The definitive internal record of what v3.0 delivers and why it matters.**

← [Back to Framework README](../README.md) · [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/) · [Toolkit](https://cyberstrategyinstitute.com/ai-safe2/) · [GitHub Release](https://github.com/CyberStrategyInstitute/ai-safe2-framework/releases)

---

## Navigation

| Section | What It Covers |
|:---|:---|
| [The One-Line Case](#the-one-line-case) | Why v3.0 is a generational upgrade, not an increment |
| [Part I — The Framework](#part-i-the-framework-itself) | 161 controls, CP.1-CP.10 Governance OS, 23 new pillar controls, risk formula, 32 frameworks, T11 |
| [Part II — The Tool Ecosystem](#part-ii-the-tool-ecosystem) | Dashboard, Command Center, MCP Server, Gateway, Scanner, Pre-Flight Checklist |
| [Part III — First-in-Field](#part-iii-first-in-field-advantages) | CP.7 Active Defense, CP.9 Agent Replication, CP.10 HEAR Doctrine |
| [Part IV — v2.1 Preserved](#part-iv-v21-to-v30--what-was-preserved) | What carried forward unchanged |
| [Part V — Strategic Advantages](#part-v-strategic-advantages-over-every-other-approach) | vs. Detection-first · vs. Checklist compliance · vs. Single-framework · vs. Build-it-yourself |
| [Part VI — Why Now](#part-vi-why-now--the-urgency-case) | Active threats, regulation timeline, deployment wave, zero time-to-value |
| [Audience Summary](#summary-the-v30-value-proposition-by-audience) | One-row value statement per role |

---

## The One-Line Case

v3.0 is not an incremental update. It is a generational upgrade that transforms AI SAFE² from a control catalog into a complete governance operating system for autonomous AI — with tooling, interactive infrastructure, three first-in-field standards, and now a production-grade enforcement gateway that closes the gap between where controls are documented and where attackers actually operate.


[↑ Navigation](#navigation)

---

## Part I: The Framework Itself

### Scale and Completeness

**161 total controls** — up from 128 in v2.1. That is a 26% increase in coverage, but the number understates the shift. The 33 new controls are not marginal additions. They target the attack surfaces that emerged from 2025-2026 real-world agentic deployments: multi-session behavioral conditioning, cloud AI platform configuration attacks, agent replication without governance, RAG corpus poisoning that activates weeks after implantation, and the absence of any named human with kill-switch authority over autonomous agents.

**Breakdown:**

| Version | Controls | What They Address |
|:---|:---|:---|
| v2.0 | 98 controls | Core AI security fundamentals across 5 pillars |
| v2.1 | +30 gap fillers | Agentic systems, NHI, multi-agent, memory poisoning, swarm |
| v3.0 new pillar | +23 controls | The attack surfaces that emerged from production agentic deployments |
| v3.0 CP Governance OS | +10 controls | Cross-pillar governance layer — none of this existed before |
| **Total** | **161 controls** | **The most complete agentic AI governance standard available** |

---

### The Cross-Pillar Governance OS — CP.1 through CP.10

This is the architectural innovation of v3.0. Every framework before this — NIST AI RMF, ISO 42001, OWASP, CSA, EU AI Act — operates at the pillar or control level. None of them defined a governance layer that sits *above* all pillars, applies *across* all pillars simultaneously, and enforces *at the execution layer*. AI SAFE² v3.0 does.

CP.1 through CP.10 is not a sixth pillar. It is a governance operating system that binds the five pillars together and defines the policy enforcement architecture for autonomous agents.

**CP.1 — Agent Failure Mode Taxonomy**
Every agentic incident must be tagged with `cognitive_surface=(model|memory|both)` and `memory_persistence=(session|cross_session)`. This separates ordinary prompt failures from belief drift and memory corruption — two attack classes that had no formal classification before this. Without this taxonomy, post-mortems label everything "agent error" and no learning occurs.

**CP.2 — Adversarial ML Threat Model Integration**
Mandatory governance artifact for ACT-2+ deployments. The breakthrough: every threat must carry a `temporal_profile=(immediate|delayed_days|delayed_weeks|chronic)`. This is the first framework to formally require time-shifted attack modeling. A RAG poisoning campaign planted three weeks ago that activates today cannot be captured by per-session threat models. CP.2 forces teams to think in campaigns, not incidents.

**CP.3 — ACT Capability Tiers 1-4**
Formal four-tier agent classification system: Assisted, Supervised, Autonomous, Orchestrator. Each tier has mandatory controls, escalating governance requirements, and defined deployment blockers. Before CP.3, there was no industry standard for "what level of autonomy does this agent have?" — security reviews were guessing. Now there is an answer with enforcement.

**CP.4 — Agentic Control Plane Governance**
Defines the Agentic Control Plane — agent identity, dynamic permission enforcement, orchestration boundaries, runtime behavioral trust — as a board-visible governance artifact. A2A, MCP, and ACP protocol meshes must be evaluated against CP.3 through CP.7. This translates what was purely an engineering concept into governance language the board can act on.

**CP.5 — Platform-Specific Agent Security Profiles**
The first per-platform companion standard in any AI governance framework. Bedrock, Azure AI Foundry, n8n, LangGraph, AutoGen, and CrewAI each have distinct attack surfaces. Generic guidance does not tell a Bedrock operator which specific APIs to monitor. CP.5 does.

**CP.6 — AI Incident Feedback Loop Integration**
Quarterly AIID agentic incident reviews plus a 30-day Incident-Informed Control Review triggered by any new relevant AIID incident. Requires an internal Agentic Incident Registry. This closes the gap between the broader AI incident ecosystem and an organization's own control posture — a gap that previously required manual intervention to close.

**CP.7 — Deception & Active Defense Layer (First in Field)**
The only deception-class control in any AI governance framework, anywhere. Canary documents in RAG corpora detect injection attempts before they succeed. Honeypot tool endpoints identify tool squatting. Fake credential traps in agent memory catch exfiltration attempts. Every other framework is purely defensive — detect after the fact. CP.7 shifts posture to active: catch attackers in the act of reconnaissance, before they achieve their objective.

**CP.8 — Catastrophic Risk Threshold Controls**
Documents the behavioral indicators that trigger emergency agent suspension *regardless of business continuity impact*. Unauthorized compute acquisition. Communication outside the approved endpoint list. Evidence of weaponizable capability. This is a hard deployment blocker for ACT-3 and ACT-4 — no deployment approval without CRT documentation. The industry had no formal definition of "when do we halt regardless of cost." Now it does.

**CP.9 — Agent Replication Governance (First in Field)**
The only governance standard for agent replication anywhere in the world. NIST, ISO, OWASP, and enterprise IAM frameworks have zero coverage of this attack surface. When an orchestrator spawns sub-agents, there has been no standard for: lineage tokens, delegation hop limits, credential scope narrowing per hop, or kill-switch SLAs for delegation trees. CP.9 defines all of it with hard specs: max 2 hops for ACT-3, max 3 for ACT-4, 500ms full delegation-tree severance on kill signal, ephemeral credentials with scope narrowing per hop. This is not abstract guidance — it is an implementable specification with SLAs.

**CP.10 — HEAR Doctrine (First in Field)**
The only framework to define named individual accountability with cryptographic enforcement at the execution layer. A Human Ethical Agent of Record is a specific named individual — not a team, not a role — with a cryptographic signing key registered before deployment. Class-H actions (irreversible, financially material, security-control-modifying, physical-infrastructure-crossing, cross-organizational) require the HEAR's cryptographic signature before execution. Fail-closed: if the HEAR is unreachable, Class-H actions are blocked. No automatic approval path. This is the answer to the question "when something goes catastrophically wrong, who has the authority and the mechanism to stop it?" Before CP.10, the answer was "unclear." After CP.10, it is a named person with a key.

---

### 23 New Pillar Controls — What They Solve

**Pillar 1 — Six new sanitization and isolation controls:**

*P1.T1.10 — Indirect Injection Surface Coverage:* The first control to formally require enumeration and sanitization of every non-prompt input channel — emails, tool outputs, retrieved documents, API responses. Most injection defenses focus on the user chat interface. Indirect injection exploits every other surface the agent touches. This closes that gap.

*S1.3 — Semantic Isolation Boundary Enforcement:* Architecturally separates trusted system instruction context from untrusted content processing at the inference layer. Agents that retrieve external content and process it in the same context as their instructions are vulnerable to context contamination. S1.3 requires the architectural separation that prevents this class of attack.

*S1.4 — Adversarial Input Fuzzing Pipeline:* Moves adversarial testing from a pre-deployment checkbox into a mandatory CI/CD gate triggered by every model update, prompt change, and tool addition. The agent that was tested at launch is not the same agent running three months later.

*S1.5 — Memory Governance Boundary Controls:* Every write to persistent agent memory requires authorization, sanitization with input-equivalent rigor, and an append-only audit log entry. Before this control, RAG corpora and agent memory stores were write-accessible to any process with permissions. S1.5 treats memory writes with the same rigor as code deployments.

*S1.6 — Cognitive Injection Sanitization:* Semantic intent analysis that detects multi-turn behavioral conditioning, role confusion, and few-shot pattern implanting — the attack class that bypasses per-message injection filters entirely. This is the detection control for T11 Multi-Turn Behavioral Conditioning, a threat category that did not exist in v2.1.

*S1.7 — No-Code / Low-Code Platform Security:* The first dedicated governance standard for n8n, Zapier, Power Automate, and similar platforms. CVE-2026-25049 is actively exploited. These platforms represent the largest unaddressed attack surface in enterprise AI deployments because they sit outside traditional security tooling and reviews.

**Pillar 2 — Four new audit and inventory controls:**

*A2.3 — Model Lineage Provenance Ledger:* Cryptographic chain of custody from base model through every fine-tuning stage to production. Extends OpenSSF OMS. Answers the question auditors now ask: "Can you prove which training data produced the model currently in production?"

*A2.4 — Dynamic Agent State Inventory:* Real-time registry of every deployed agent with `owner_of_record`, ACT tier, tool authorizations, `hear_agent_of_record`, and `control_plane_id`. The baseline for answering "how many agents are running right now?" — a question most organizations currently cannot answer.

*A2.5 — Semantic Execution Trace Logging:* Full agent execution trace — reasoning chain, every tool call with parameters, every memory operation — written to an append-only store the agent cannot modify. The difference between "something went wrong" and "here is exactly what the agent was reasoning at 14:32:07 when it made the decision." Required for ACT-2+.

*A2.6 — RAG Corpus Diff Tracking:* Hash-verified change log for the retrieval layer that automatically correlates behavioral changes to corpus changes. The control that answers "my agent started giving different answers after someone updated the knowledge base — can I prove the connection?" Closes the gap between corpus management and agent behavior observability.

**Pillar 3 — Four new fail-safe controls:**

*F3.2 — Agent Recursion Limit Governor:* Hard cap on tool-calling depth enforced at the API gateway layer — not the system prompt. Default maximum depth of 4. Fail-closed. A system prompt recursion limit can be bypassed by prompt injection. A gateway-layer limit cannot.

*F3.3 — Swarm Quorum Abort Mechanism:* Decentralized threshold-based abort: when a configurable quorum of swarm agents agree the task should stop, coordinated shutdown proceeds without a centralized kill signal. Addresses the specific failure mode where stopping the orchestrator does not stop its worker agents.

*F3.4 — Behavioral Drift Baseline and Rollback:* Establishes measurable behavioral baselines with defined probe sets and automated rollback when drift exceeds configurable thresholds. The detection and response control for behavioral drift — catches conditioning campaigns and model degradation before users surface it.

*F3.5 — Multi-Agent Cascade Containment:* Limits the blast radius of agent failures in pipeline and orchestrator architectures. Failed agents are isolated at their boundary so downstream agents receive clean error signals instead of propagating failure state.

**Pillar 4 — Five new monitoring controls:**

*M4.4 — Adversarial Behavior Detection Pipeline:* Continuously probes deployed agents with adversarial inputs and monitors behavioral responses. Attack patterns from the red-team artifact repository (E5.4) feed detection rules automatically. Moves from reactive anomaly detection to proactive adversarial monitoring.

*M4.5 — Tool-Misuse Detection Controls:* Establishes tool invocation baselines and detects tool squatting, unexpected tool calls, anomalous parameters, and invocation frequency spikes. Tool squatting — where a malicious tool registers under a legitimate-sounding name — was undetected before this control.

*M4.6 — Emergent Behavior Anomaly Detection:* Classifies behavioral novelty — new task types, unexpected tool sequences, systematic decision bias — as security-relevant signals requiring governance review. An agent that developed a capability it was not programmed with is a security event, not a feature.

*M4.7 — Jailbreak and Injection Telemetry Layer:* Unified logging and classification for all jailbreak attempts by technique: direct injection, indirect injection, cognitive injection, encoding bypass. Feeds the E5.4 artifact repository. Organizations previously saw only successful attacks. M4.7 surfaces the probing and reconnaissance activity that precedes them.

*M4.8 — Cloud AI Platform-Specific Monitoring:* Monitors the Bedrock `UpdateGuardrail` and `UpdateDataSource` APIs and Azure AI Foundry configuration changes — attack paths that standard CloudTrail monitoring misses. The Bedrock Guardrail poisoning path via `UpdateGuardrail` was confirmed active before this control was written.

**Pillar 5 — Four new evolution and education controls:**

*E5.1 — Continuous Adversarial Evaluation Cadence:* Mandatory evaluation gates triggered by model updates, prompt changes, tool additions, and quarterly cadence — not just launch. The framework that was tested at deployment is not the framework running today.

*E5.2 — Capability Emergence Review Process:* Structured four-tier governance for emergent agent capabilities: Tier 1 document, Tier 2 security review, Tier 3 board approval, Tier 4 suspend pending investigation. The industry had no formal process for "my agent started doing something I did not design."

*E5.3 — Evaluation-Safe Pattern Library:* Validated reference implementations for all AI SAFE² controls with platform-specific variants for Bedrock, Azure AI, LangGraph, AutoGen, n8n, and CrewAI. Every team solving the same security engineering problem from scratch is institutional waste. E5.3 eliminates it.

*E5.4 — Red-Team Artifact Repository:* Structured schema for all red-team findings, required as a deliverable from every exercise, integrated into the E5.1 evaluation cadence for continuous reuse. Red-team findings that sit in a PDF nobody reads are not institutional knowledge. They become institutional knowledge when they feed the next exercise automatically.

---

### Risk Formula — The OWASP AIVSS Integration

v3.0 is the first framework to integrate the OWASP AIVSS v0.8 Agentic Amplification Factor into a GRC risk formula:

```
Combined Risk Score = CVSS_Base + ((100 - Pillar_Score) / 10) + (AAF / 10)
```

**Why this matters over standard CVSS alone:**

Standard CVSS scores a vulnerability in isolation. It has no mechanism to account for the fact that the same vulnerability in an autonomous agent with persistent memory, broad tool access, and no human checkpoints is categorically more dangerous than the same vulnerability in a read-only chatbot. The AAF captures 10 agentic amplification factors — autonomy level, tool access breadth, context persistence, behavioral determinism, state retention, and five others — each scored 0 to 10.

A CVSS 7.5 vulnerability in a chatbot might score 8.5 combined. The same vulnerability in a fully autonomous orchestrator with uncontrolled AAF factors might score 19+. That is the difference between "schedule a patch" and "do not deploy until this is fixed." Standard GRC frameworks cannot make that distinction. v3.0 can.

---

### Compliance Coverage — 32 Frameworks

Up from approximately 14 in v2.1. Added in v3.0:

AI-specific additions: OWASP AIVSS v0.8, OWASP Agentic Top 10, CSA Zero Trust for LLMs, MAESTRO (CSA 7-layer), Arcanum PI Taxonomy, AIDEFEND, AIID Agentic Incidents, International AI Safety Report 2026, MIT AI Risk Repository v4, CSETv1.

Enterprise additions: DORA, SEC Cybersecurity Disclosure, CCPA/CPRA, CVE/CVSS.

**The practical advantage:** A single AI SAFE² v3.0 implementation produces compliance evidence for ISO 42001, NIST AI RMF, EU AI Act, SOC 2, HIPAA, GDPR, FedRAMP, CMMC 2.0, DORA, SEC Disclosure, and 22 additional frameworks simultaneously. Organizations using point solutions for each framework rebuild the same evidence multiple times. AI SAFE² v3.0 does it once.

---

### New Threat Category — T11 Multi-Turn Behavioral Conditioning

The AISM Agent Threat Control Matrix now covers 11 threat categories. T11 is the first new category added to the matrix.

**Why it required its own category and could not fold into T1 Prompt Injection:**

T1 is detectable at the input boundary on a per-message basis. T11 operates across many sessions, planting behavioral patterns that persist independently of the original attack inputs. No individual message appears adversarial. Detection requires semantic analysis across multiple sessions, baseline drift detection (F3.4), cross-session trace analysis (A2.5), and CP.2's temporal profile field — all of which are different tools from per-message injection detection.

The attack vectors covered: few-shot pattern implanting across sessions, role confusion over multiple interactions, contextual anchoring in early sessions to bias later responses, persona drift, and belief injection into persistent context. The detection and response controls are S1.6, F3.4, A2.5, and CP.2 — none of which were in v2.1.


[↑ Navigation](#navigation)

---

## Part II: The Tool Ecosystem

### Interactive Dashboard — 161 Controls, Zero Install

The free dashboard shipped with v3.0 is a single HTML file that runs entirely in the browser with no build step, no server, no dependencies. This is not a documentation site. It is an interactive governance instrument.

**Persona routing:** Six distinct lenses — Executive, Architect, Builder, GRC, Researcher, Explorer — each routing to a different view of the same 161 controls. The board member and the developer are not looking for the same thing. They get different default views without any configuration.

**ACT Tier Classifier:** Six questions determine the agent's ACT tier and return the mandatory control set, HEAR requirement flag, CP.9 flag, and CP.8 catastrophic risk threshold requirement — all from a single interactive flow. What previously required reading the framework documentation and manually cross-referencing controls is now a 90-second interactive process.

**CP.1-CP.10 Governance OS section:** The cross-pillar controls appear as a dedicated amber-highlighted band at the top of the architect matrix, separate from the pillar controls. This is the visual architecture decision that reflects the governance OS concept — CP controls are not just another filter category, they are a distinct layer.

**Live risk calculator:** CVSS + Pillar + AAF composite scoring in real time. Sliders. Instant result. No spreadsheet required.

**Compliance crosswalk:** All 32 frameworks. Select any framework, get every AI SAFE² control mapped to it. Filter to OWASP Agentic Top 10, EU AI Act, or DORA and see exactly which controls satisfy each. This replaces a compliance mapping exercise that previously took days.

**Pre-Flight Checklist CTA in Builder lens:** Two conversion touchpoints — one at peak desire immediately after the ACT Tier Classifier result, one standalone block between the control matrix and the scanner CTA. The placement logic: the user just learned what governance they need. The next question is "am I ready to ship?" The checklist answers that question.

**Dark/light mode:** Full CSS variable swap with localStorage persistence. Radar graph colors are theme-aware — `gridCol` and `axisCol` computed from `this.dark` state at render time.

**No-build deployment:** `dashboard/index.html` on GitHub Pages. Alpine.js + Tailwind CDN. No build pipeline. No server. Update the embedded `CONTROLS_DATA` constant and push.

---

### Risk Command Center — Board Decision Instrument

The paid Command Center is the governance artifact that makes the free dashboard's assessment actionable at the executive level.

**Import from free dashboard:** One-way JSON import from the free dashboard assessment. The user completes their assessment in the free tool, copies the JSON, pastes it into the Command Center. Scores, org name, ACT tier, CVSS, and AAF load automatically. This is the upgrade funnel built into the architecture itself.

**Business language layer:** Every control recommendation has a `boardImpact` field in plain English. Every persona — CISO, Board/Executive, GRC/Compliance, Owner/Risk Officer — gets different text panels, different board questions, different language on the same data. The board does not need to understand what CP.10 is. They need to understand what it means for the organization's liability posture.

**Board Brief tab:** Five dynamically generated bullets plus "Recommended Board Action" plus persona-specific questions — all driven by the slider inputs, not hardcoded. A CISO gets different board questions than a GRC officer reviewing the same posture.

**Hexagonal six-axis radar:** Visualizes P1-P5 plus CP as a sixth axis. The CP axis is the v3.0 innovation — it did not exist in v2.1 because there were no cross-pillar controls to score. The radar makes the gap between current posture and full compliance immediately visible to a non-technical audience.

**Compliance readiness tab:** 10 frameworks with READY/PARTIAL/GAP status driven by pillar scores. Shows exactly which frameworks the organization is positioned to certify for and which have blocking gaps.

**Full remediation roadmap:** Autogenerated across all six governance areas — not a static template but a dynamic output from the slider state.

---

### MCP Server — Claude Code Integration

The AI SAFE² MCP server brings the entire 161-control governance framework into Claude Code and any MCP-compatible AI coding assistant. Seven tools with tiered access:

**`lookup_control`:** Search all 161 controls by keyword, pillar, priority, framework mapping, ACT tier, or exact ID. Free tier: 30 results. Pro tier: 500 results across all 32 frameworks.

**`risk_score`:** Live Combined Risk Score calculation. Free tier: CVSS + Pillar only. Pro tier: full AAF with all 10 OWASP AIVSS factors, governance failure flagging, and control recommendations.

**`compliance_map`:** Maps a compliance requirement to AI SAFE² controls. Free tier: 5 frameworks. Pro tier: all 32.

**`code_review`:** Returns the relevant control taxonomy and structured findings template for the model to use in reasoning about the submitted code. No server-side code execution — model-assisted analysis against the control set. Pro only.

**`agent_classify`:** Six signals in, ACT tier out — with mandatory controls, HEAR requirement, CP.9 flag, governance evidence package, and next steps. Free tier: ACT-1/ACT-2 only. Pro tier: full ACT-1 through ACT-4 with complete CP governance requirements.

**`get_governance_resource`:** Policy templates, audit scorecard schema, HEAR designation form, quick-start checklist, pillar overview. Free tier: 3 resources. Pro tier: full governance package.

**`get_workflow_prompt`:** Four pre-built workflow prompts — security architecture review, compliance gap analysis, incident response runbook, agent deployment checklist. Available to all tiers.

**Dual transport:** `stdio` for local Claude Code use (no auth, no network, inherently secure). HTTPS via Caddy sidecar for remote deployment (bearer token, localhost-only binding, TLS termination external). No HTTP. No plain text. No self-signed certs in production.

**51 passing tests.** The MCP server ships production-ready, not as a prototype.

---

### Scanner v3.0 — CI/CD Code Analysis

40+ rules covering all 5 pillars and CP.1-CP.10. AST-based analysis. SARIF output for GitHub Advanced Security and enterprise SIEM integration. ACT tier estimation from code structure. Maps findings to all 32 frameworks.

**What v3.0 adds over the prior scanner:** Indirect injection surface detection (P1.T1.10), memory governance gap detection (S1.5), recursion limit absence detection (F3.2), tool-misuse baseline absence (M4.5), and HEAR requirement detection for ACT-3/4 code patterns.

---

### AI Builder Pre-Flight Checklist

35 structured questions organized across 7 categories: Input Defense, Data Governance, Human Oversight, Fail-Safe Design, Audit and Logging, Compliance, and ACT Tier Gates. Each question maps directly to an AI SAFE² v3.0 control.

**The v3.0 advantage:** v2.1 had no formal pre-deployment readiness assessment. The Pre-Flight Checklist operationalizes the governance requirements into a ship/no-ship decision tool. It is free — permanently — because zero-friction access to the checklist drives awareness and upstream demand for the paid toolkit.

**CTA integration in the dashboard:** The checklist CTA appears at two moments in the Builder lens — immediately after the ACT Tier Classifier result (peak desire: the user knows what they need and the next question is "am I ready?") and as a standalone block with sample questions and category coverage visible before clicking.

---

### AI SAFE² Control Gateway — Production-Grade Enforcement at the Execution Boundary

**Release:** [April 14, 2026 — Gateway Enforcement Update v3.0](https://github.com/CyberStrategyInstitute/ai-safe2-framework/releases/tag/2026-04-14_Gateway_Enforcement_Update_v3.0)

Every other component of the AI SAFE² ecosystem — the framework, the dashboard, the scanner, the MCP server — operates in the design and assessment layer. The Gateway is different. It operates at the execution boundary: the moment a request leaves an application and reaches an LLM provider. That is the only point where deterministic enforcement is architecturally possible.

The problem the gateway solves is not missing controls. The industry has no shortage of controls on paper. The problem is placement. Controls that live in documentation, system prompts, or periodic audits are outside the execution boundary. Attackers operate inside it. The gateway closes that gap.

**Multi-Provider Enforcement — One Config, Identical Policy Across All Providers**

Most teams today are running provider-specific integration logic: different API client code for Anthropic, OpenAI, Gemini, Ollama, and OpenRouter. Different error handling. Different response formats. Different behavioral characteristics. Different risk surfaces. Each provider integration is a separate governance problem.

The gateway collapses this into a unified control plane. Anthropic, OpenAI/Codex, Gemini, Ollama (local), and OpenRouter are all supported. One config change switches providers. Enforcement — rate limiting, validation, logging, HITL circuit breaking — stays identical across all of them. A team that adds a second provider does not build a second governance layer. They inherit the existing one.

The underlying architecture: `provider_adapters.py` normalizes every provider's request and response format into a single internal schema before enforcement logic runs. Provider-specific behavior is an adapter concern, not a policy concern.

**Deterministic Execution Gating — Heartbeat-Linked Validation Before Every Request**

The gateway validates system integrity before every LLM call via a `GENESIS_HASH` derived from SHA-256 of the gateway configuration at startup. This hash is checked on each heartbeat. If the hash is missing, stale, or has been tampered with, the gateway stops — hard stop, no fallback behavior, no graceful degradation into an unvalidated execution path. The integrity check is not a logged warning. It is a gate.

This is the architectural expression of the core axiom: you cannot govern what you cannot verify. Governance that proceeds when integrity cannot be confirmed is not governance — it is optimism.

**Provable System Integrity — HMAC-SHA256 Chained Audit Logs**

Every request is logged. Every provider is tracked. Every response is recorded. The log is HMAC-SHA256 chained — each entry includes a hash of the previous entry. Tamper with any entry and the chain breaks. Chain break triggers safe mode automatically. The audit trail is not just a record of what happened — it is a cryptographic proof that the record has not been altered.

This satisfies A2.5 (Semantic Execution Trace Logging) at the infrastructure layer rather than requiring application-layer instrumentation. The gateway produces the append-only, tamper-evident audit trail that A2.5 requires as a mandatory control for ACT-2+ deployments.

**Runtime-Aware Risk Scoring — Action × Sensitivity × Context**

Static risk thresholds fail in dynamic agentic environments because the same action carries different risk depending on context. The gateway implements runtime-aware risk scoring using the formula: `Action × Sensitivity × Historical Context` with modifiers for detected prompt injection (+5) and A2A impersonation detection (+3).

This is a runtime implementation of the Combined Risk Score concept from the framework — not a periodic assessment but a per-request calculation that adjusts to what is actually happening in the execution stream. A high-sensitivity action from an agent with a clean history scores differently from the same action preceded by an injection attempt.

**Programmable Human Escalation — 4-Tier HITL Circuit Breaker**

The gateway implements a four-tier Human-in-the-Loop circuit breaker that operationalizes CP.10 at the infrastructure layer:

| Tier | Risk Threshold | Escalation Mechanism |
|:---|:---|:---|
| LOW | Baseline | Proceed, log |
| MEDIUM | Elevated | Proceed with enhanced logging |
| HIGH | Significant | Queue for async human review |
| CRITICAL | Maximum | Hard stop — requires out-of-band HMAC 2FA before proxy |

CRITICAL tier is the gateway implementation of CP.10 Class-H action protocol. The request stops. It does not proceed until an out-of-band HMAC 2FA confirmation is received. No token, no proxy. The HEAR doctrine is not a policy artifact at this tier — it is an enforced gate in the request pipeline.

**Bidirectional Enforcement — Requests Gated, Responses Inspected**

Most API security tooling is unidirectional — it inspects requests going out. The gateway enforces bidirectionally. Requests are gated before they reach the provider. Responses are inspected before they reach the application. Provider response formats are normalized into a unified schema for detection logic, so a response anomaly from Gemini and the same anomaly from Anthropic trigger identical detection rules. Provider diversity does not create detection coverage gaps.

**NEXUS-A2A v0.2 Ready — Identity Passthrough and Delegation Chain Logging**

The gateway ships with NEXUS-A2A v0.2 compatibility hooks enabled by default: header detection for agent identity passthrough, delegation chain logging for CP.9 lineage tracking, and passthrough enforcement mode. Full NEXUS-A2A enforcement activates with a single config flag — `nexus_a2a_enforcement: true`. For teams not yet running NEXUS-A2A, the hooks are present and logging. For teams running it, enforcement is config-change-away rather than a new integration.

**48 Passing QA Tests**

The gateway QA test suite grew from its initial state to 48 passing tests covering multi-provider adapters, GENESIS_HASH integrity validation, HMAC chain integrity, HITL circuit breaker tiers, risk scoring with modifiers, NEXUS-A2A passthrough, and bidirectional inspection. The gateway ships production-ready.

**Key technical fix included in this release:** The `GENESIS_HASH` initialization bug where the hash was derived as a colon-delimited string that failed the regex validator on the first heartbeat check — causing valid gateway instances to immediately enter safe mode on startup — is resolved. The hash is now correctly derived from SHA-256 of the configuration payload, passes the validator, and heartbeat operates as designed.

**What this means for the v3.0 posture argument:**

The detection-vs-enforcement distinction that runs through the framework's strategic positioning is now not just a principle — it is a shipped artifact. Detection finds threats after execution. Enforcement determines whether they execute at all. The gateway is the enforcement layer that makes that statement operationally true rather than aspirationally true.


[↑ Navigation](#navigation)

---

## Part III: First-in-Field Advantages

Three controls in AI SAFE² v3.0 are the first of their kind in any published AI governance framework:

### CP.7 — First Deception-Class AI Governance Control
No other framework — NIST AI RMF, ISO 42001, EU AI Act, OWASP, CSA, MITRE ATLAS — defines an active defense strategy for AI systems. They all assume a detection-first posture. CP.7 shifts to offense-informed defense: plant canaries in the RAG corpus, honeypots in the tool registry, credential traps in agent memory, and detect attackers in the reconnaissance phase before they achieve their objective.

### CP.9 — First Agent Replication Governance Standard
The orchestrator-spawns-sub-agent pattern is one of the most widely deployed architectures in enterprise AI (LangGraph, AutoGen, CrewAI, n8n agent loops). It is also completely ungoverned by every existing framework. CP.9 is the first published governance standard for this pattern: lineage tokens, delegation hop limits, ephemeral credentials per hop, and a 500ms kill-switch SLA for the full delegation tree. This is implementable. It has SLAs. It has per-tier limits.

### CP.10 — First Named Individual Accountability with Cryptographic Enforcement
Human oversight provisions in the EU AI Act (Articles 9 and 14), NIST AI RMF, and ISO 42001 all require "human oversight" without specifying who, how fast, by what mechanism, or what happens when the human is unavailable. CP.10 answers all four: a named individual, in real time, via cryptographic signing, fail-closed. It is the first framework to translate regulatory intent into operational engineering requirements.


[↑ Navigation](#navigation)

---

## Part IV: v2.1 to v3.0 — What Was Preserved

Every v2.1 advantage carries forward in v3.0. This is not a replacement — it is an upgrade. All 128 controls from v2.1 are present and referenced correctly by ID. The v3.0 schema adds `builder_problem`, `act_minimum`, `version_added`, and `first_in_field` fields to each control, making the data richer without breaking any existing reference.

The architectural philosophy is unchanged: prevention-first over detection-first, deterministic enforcement over probabilistic detection, engineered certainty over reactive hope. v3.0 extends that philosophy deeper into the agentic attack surface with specific mechanisms where v2.1 had principles.


[↑ Navigation](#navigation)

---

## Part V: The Strategic Advantages Over Every Other Approach

### Against Detection-First Frameworks (Most of the Market)

Detection-first frameworks (SIEM tuning, anomaly detection, log analysis) assume the attack has already happened and focus on minimizing dwell time. For agentic systems with write access, financial authority, and the ability to spawn sub-agents, dwell time is not the right metric. An autonomous agent can exfiltrate, corrupt, and cover tracks in seconds. Detection after the fact is governance theater.

AI SAFE² v3.0 enforces at machine speed at the architectural layer — the Control Gateway gates every LLM request before it executes, with runtime risk scoring and a 4-tier HITL circuit breaker that stops CRITICAL requests cold until out-of-band HMAC 2FA is confirmed. Below the gateway: gateway-enforced recursion limits (F3.2), memory write authorization (S1.5), semantic isolation at the inference layer (S1.3). The attack surface that does not exist cannot be exploited. The request that does not execute cannot cause harm.

### Against Checklist Compliance (Most GRC Approaches)

Static compliance checklists — "do you have a policy for X?" — do not distinguish between a policy that exists and a control that is enforced. AI SAFE² v3.0 requires deterministic enforcement: controls at the API gateway layer, not the system prompt. Controls in the deployment manifest, not the documentation. HEAR designation with cryptographic keys, not a name in a spreadsheet.

The AISM maturity matrix (AISM) provides quantitative measurement of control implementation depth — not checkbox status but actual enforcement level. This is the difference between "we have a kill switch policy" and "we have a cryptographically enforced HEAR with 500ms SLA."

### Against Single-Framework Approaches (NIST Only, ISO Only)

An organization that implements only NIST AI RMF covers governance and risk management but has no coverage for agent replication, active defense, behavioral conditioning attacks, or cloud AI platform-specific attack paths. An organization implementing only ISO 42001 has strong management system requirements but no operational controls for autonomous agent behavior.

AI SAFE² v3.0 maps to 32 frameworks simultaneously. One implementation, one evidence package, 32 compliance checkboxes. The compliance crosswalk in the dashboard shows which controls satisfy which framework requirements — auditors get the evidence in the format they need, not a mapping exercise.

### Against Build-It-Yourself Governance

Most organizations encountering autonomous agents are solving the same governance problems from scratch: "how do we classify this agent?" (CP.3 answers this), "who is accountable when something goes wrong?" (CP.10 answers this), "how do we stop a runaway orchestrator that has spawned sub-agents?" (CP.9 answers this). Each team is building governance from first principles.

AI SAFE² v3.0 collapses that discovery process into an interactive ACT Tier Classifier (six questions, instant output), a governance evidence package, a deployment checklist, and an MCP server that brings the framework into the AI coding assistant the team is already using.


[↑ Navigation](#navigation)

---

## Part VI: Why Now — The Urgency Case

**The attack surface materialized in 2025-2026.** CVE-2026-25049 (n8n active exploitation) is the most visible example, but M4.8 was written in response to confirmed Bedrock UpdateGuardrail attacks in production. The threat categories in v3.0 are not theoretical — they are documented, active, and unaddressed by every framework that predates this release.

**Regulation is arriving faster than most organizations are implementing.** EU AI Act enforcement has begun. SEC cybersecurity disclosure requirements apply to material AI incidents. DORA covers AI system resilience for financial entities. Each of these regulations requires evidence of governance — not intention, not roadmaps, but implemented controls with documented accountability. CP.10 HEAR designation satisfies EU AI Act Articles 9 and 14 human oversight requirements, SOC 2 CC.7.4, GDPR Article 22 automated decision safeguards, and SEC accountability standards simultaneously.

**The agentic deployment wave is outrunning governance.** LangGraph, AutoGen, CrewAI, and n8n adoption is accelerating. Every team deploying these frameworks is inheriting the full CP.9 attack surface — unbounded delegation chains, untracked sub-agent proliferation, no kill-switch SLA — without knowing it. The governance gap is not visible until an incident makes it visible.

**v3.0 is deployable today.** No procurement cycle. No vendor relationship. The free dashboard is live on GitHub Pages. The scanner integrates into any CI/CD pipeline with a single command. The MCP server connects to Claude Code in under five minutes via stdio. The Control Gateway is available in the repository and connects to Anthropic, OpenAI, Gemini, Ollama, and OpenRouter with 48 passing tests and production-ready HMAC audit logging. The Pre-Flight Checklist is a download. The paid toolkit is available immediately at checkout. There is no time-to-value lag.


[↑ Navigation](#navigation)

---

## Summary: The v3.0 Value Proposition by Audience

| Audience | What v3.0 Delivers |
|:---|:---|
| **Security Architect** | 33 new controls targeting real 2025-2026 attack surfaces. CP.7 active defense. Platform-specific monitoring (M4.8) for Bedrock and Azure AI Foundry attacks. T11 threat category with detection controls. Control Gateway with HMAC-chained audit logs, runtime risk scoring, and 4-tier HITL circuit breaker — enforcement at the execution boundary, not the documentation layer. |
| **Developer / Builder** | ACT Tier Classifier in 6 questions. Pre-Flight Checklist before every deploy. MCP server in Claude Code for real-time governance guidance. Control Gateway for multi-provider enforcement with 48 passing tests and NEXUS-A2A v0.2 compatibility. Scanner in CI/CD for automated control gap detection. |
| **GRC / Compliance** | 32 frameworks from a single implementation. Live compliance crosswalk in the dashboard. Board Brief generator in the Command Center. Evidence package built from assessment output. |
| **CISO** | HEAR doctrine solves named accountability. CP.8 catastrophic risk thresholds give deployment authority structure. Combined Risk Score with AAF translates technical posture into board-consumable numbers. |
| **Board / Exec** | Hexagonal posture radar. Risk Score in plain language. Board Brief with "Recommended Board Action." 32-framework coverage status. Named HEAR accountability for autonomous deployments. |
| **Red Team** | T11 behavioral conditioning as a formal threat category. CP.7 active defense architecture to attack and validate. M4.7 jailbreak telemetry layer shows what reconnaissance your platform is currently failing to detect. E5.4 artifact repository structure for institutional red-team knowledge. |

---

*AI SAFE² v3.0 — Engineered Certainty for the AI Era.*
*Cyber Strategy Institute | cyberstrategyinstitute.com*
