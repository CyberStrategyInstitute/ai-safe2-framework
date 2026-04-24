# Cross-Pillar Governance Layer
### ⚙️ The Governance OS

[![Cross-Pillar Governance Layer (CP.1–CP.10)](https://img.shields.io/badge/Cross--Pillar-Governance_Layer_CP.1--CP.10-cc6600?style=for-the-badge&labelColor=black)](./README.md)

[🔙 Back to Main Framework](../README.md) | [← Pillar 5: Evolve & Educate](../05-evolve-educate/README.md) | [AISM Layer →](../AISM/)

---

## 🎯 The Problem. The Realization. The Solution.

**Problem:** AI agents are being deployed with no formal governance contract. No standard defines who can authorize an agent to clone itself. No standard defines who has the authority and the cryptographic capability to stop a misbehaving autonomous agent. No standard tells boards and regulators what governance evidence should look like for autonomous AI. Organizations are building agent swarms where one agent can become a thousand identities before any SIEM alert fires, and there is no defined accountability layer when something goes catastrophically wrong.

**Realization:** The five pillars cover the operational lifecycle of individual agents and agent systems. What was missing was a governance layer that transcends the pillars: one that defines the authority structures, the accountability primitives, the scoring mechanisms, and the catastrophic risk controls that apply across all deployments, all architectures, and all agent types. This layer cannot live inside a single pillar because it governs the interaction between all of them.

**Solution:** The Cross-Pillar Governance Layer (CP.1 through CP.10) is the governance operating system for AI SAFE² v3.0. It defines how agents are classified and governed at scale (CP.3 ACT Tiers, CP.4 Agentic Control Plane), how the framework scores risk quantitatively (CP.2, CP.3), how failures are classified and tracked across time (CP.1, CP.6), who is accountable for catastrophic failures (CP.10 HEAR Doctrine), and how agent replication — the first identity-multiplying threat in enterprise AI — is governed (CP.9 ARG).

> **What you get:** A named human with a cryptographic kill switch for every autonomous deployment. A governance tier system that satisfies boards, regulators, and compliance audits. The first formal standard for agent replication governance. A risk formula that tells you whether a vulnerability in your specific deployment context is actually critical.

---

## 🏗️ Cross-Pillar Controls Overview

![Cross-Pillar Controls v3.0](https://img.shields.io/badge/New_in_v3.0-10_Cross--Pillar_Controls-cc6600?style=flat-square)

| Control | Name | Priority | Governing |
| :--- | :--- | :--- | :--- |
| [CP.1](#cp1) | Agent Failure Mode Taxonomy | 🔴 CRITICAL | How failures are classified across all pillars |
| [CP.2](#cp2) | Adversarial ML Threat Model Integration | 🔴 CRITICAL | How threats are mapped with temporal profiles |
| [CP.3](#cp3) | ACT Capability Tiers 1-4 | 🔴 CRITICAL | How agents are classified and control requirements scaled |
| [CP.4](#cp4) | Agentic Control Plane Governance | 🔴 CRITICAL | Agent identity, delegation, orchestration, runtime trust |
| [CP.5](#cp5) | Platform-Specific Agent Security Profiles | 🟠 HIGH | Bedrock, Azure AI, n8n, and protocol-layer supply chain |
| [CP.6](#cp6) | AI Incident Feedback Loop Integration | 🟠 HIGH | AIID incident reviews and 30-day control update process |
| [CP.7](#cp7) | Deception & Active Defense Layer | 🟠 HIGH | Canary tokens, honeypot endpoints, adversarial misdirection |
| [CP.8](#cp8) | Catastrophic Risk Threshold Controls | 🔴 CRITICAL | Emergency suspension criteria regardless of business continuity |
| [CP.9](#cp9) | Agent Replication Governance | 🔴 CRITICAL | First governance standard for agent replication and swarm identity |
| [CP.10](#cp10) | HEAR Doctrine | 🔴 CRITICAL | Human Ethical Agent of Record: named kill-switch authority |

> Full control specifications — including implementation requirements, enforcement logic, compliance mappings, and ACT-tier applicability — are included in the [AI SAFE² v3.0 Implementation Toolkit](https://cyberstrategyinstitute.com/ai-safe2/).

---

<a id="cp1"></a>
## CP.1 — Agent Failure Mode Taxonomy

**What it governs:** How every agentic failure is classified so it can be triaged, remediated, and learned from consistently across all five pillars.

**The core addition:** Every agentic incident must be tagged with two cross-cutting dimensions:

- `cognitive_surface = (model | memory | both)` — did the failure root in model behavior, persistent memory, or their interaction?
- `memory_persistence = (session | cross_session)` — was the effect limited to one session or did it persist across sessions?

These tags distinguish ordinary prompt failures from belief and memory drift, which have fundamentally different remediation paths.

**Why it matters for builders:** When an incident is tagged correctly, the post-mortem is fast. The right team gets the right alert. The fix addresses the root cause, not the symptom.

---

<a id="cp2"></a>
## CP.2 — Adversarial ML Threat Model Integration

**What it governs:** A mandatory governance artifact for all ACT-2 and above deployments that maps every known threat with a temporal profile.

**The core addition:** For each mapped threat, record:

- `temporal_profile = (immediate | delayed_days | delayed_weeks | chronic)`

This captures time-shifted attacks — latent prompt poisoning, slow memory conditioning, long-horizon RAG corruption — and separates burst exploits from campaigns that play out over weeks or months.

**Why it matters for builders:** An attack planted in your RAG corpus three weeks ago activating today looks like a random agent failure without temporal profiling. With it, the timeline is traceable and the source is findable.

---

<a id="cp3"></a>
## CP.3 — ACT Capability Tiers 1-4

**What it governs:** How agents are classified by autonomy level and how mandatory control requirements scale with that classification.

| Tier | Name | Definition | Required Controls |
| :--- | :--- | :--- | :--- |
| ACT-1 | Assisted | Human reviews all outputs before action | Standard P1-P5 |
| ACT-2 | Supervised | Agent acts with human checkpoints | AAF scoring + AMLTM (CP.2) |
| ACT-3 | Autonomous | Agent operates with post-hoc review | F3.2, M4.4, CP.2, owner_of_record, HEAR required |
| ACT-4 | Orchestrator | Agent controls other agents; enterprise-scale impact | All ACT-3 + CP.4 + CP.8 + CP.9 ARG + CP.10 HEAR |

**Why it matters for builders:** Your security review will ask for ACT tier documentation before approving any autonomous deployment. Build to CP.3 now and the review is a formality.

---

<a id="cp4"></a>
## CP.4 — Agentic Control Plane Governance

**What it governs:** Agent identity, dynamic permission enforcement, orchestration boundaries, and runtime behavioral trust as an explicit governance concept.

**Key requirement:** Boards and regulators should treat the combination of Non-Human Identities (NHI) and agent orchestration as the primary control plane for autonomous AI. ACT tiers and CP.4 controls are the canonical governance evidence.

**Board-level metrics derived from CP.4:**
- Machine-to-human identity ratio (tracks NHI exposure surface)
- ACT tier distribution (ACT-3/ACT-4 concentration triggers board review)
- Owner coverage (percentage of agents with assigned owner_of_record)
- CP.4 compliance rate for ACT-3/ACT-4 agents

**Protocol assessment:** Protocol-layer meshes (A2A, MCP, ACP, and equivalents) must be evaluated against CP.3 through CP.7, not treated as isolated tools or plugins.

---

<a id="cp5"></a>
## CP.5 — Platform-Specific Agent Security Profiles

**What it governs:** Platform-by-platform security guidance with version-pinned CVE coverage and monitoring telemetry sources.

**Platforms covered:** AWS Bedrock Agents, Azure AI Foundry, n8n, LangGraph, AutoGen, CrewAI, MCP Servers, and protocol-layer meshes.

**Key requirement:** Protocol-layer meshes (A2A, MCP, ACP, and equivalents) must be assessed as first-class supply chain components with the same depth as SaaS vendors — including identity, delegation, logging, and update channels.

**Why it matters:** Platform-specific attack paths (Bedrock UpdateGuardrail API poisoning, Azure AI Foundry configuration changes) are not covered by generic cloud monitoring. CP.5 defines what to watch.

### CP.5.MCP — MCP Server Security Profile

MCP is the de facto standard for AI agent tool integration. Its STDIO transport model eliminates the network boundary that separates tool execution from host process space. Tool response data flows directly into LLM context — making the return path a first-class prompt injection surface. OX Security research (April 2026) documented RCE exposure propagating from Anthropic's official MCP SDKs to all downstream implementations. Generic platform guidance does not cover this threat class. MCP requires an explicit profile.

**Required controls:**

| ID | Control | Requirement |
| :--- | :--- | :--- |
| MCP-1 | No Dynamic Command Construction | Never pass user-controlled or tool-response-controlled input into `StdioServerParameters`, `subprocess`, `os.system`, or equivalents. Enforce via static analysis in CI/CD. |
| MCP-2 | Output Sanitization Before LLM Return | Scan all MCP tool results for prompt injection patterns — instruction-override phrases, role-confusion markers, zero-width characters, and target LLM special tokens — before returning to calling clients. Log and redact matches. |
| MCP-3 | Registry Provenance Verification | Verify all third-party MCP servers against the official GitHub MCP Registry before adding to any agent configuration. Enforce a manifest-based allowlist for approved server commands. Reject unverified sources. |
| MCP-4 | STDIO Transport Integrity Binding | For STDIO-mode deployments, verify source file hash before granting elevated tier access. Fail closed on integrity failure. |
| MCP-5 | Tool Invocation Audit Log | Every MCP tool call generates an immutable audit record (tool name, parameters, response hash, timestamp, calling agent identity) consistent with A2.5 Semantic Execution Trace Logging. Cross-reference against behavioral baseline (F3.4) to detect unexpected invocations. |
| MCP-6 | MCP Server Network Isolation | MCP servers must not have unrestricted outbound network access unless explicitly required for their defined function. Apply allowlist-based egress filtering. Block exfiltration paths to unknown external URLs. |
| MCP-7 | Zero-Trust Client Configuration | Any MCP server configuration sourced from a repository the operator does not control is treated as an untrusted artifact. Apply proxy wrapping to all third-party STDIO connections. |

**ACT tier applicability:**

- **ACT-2+:** MCP-1, MCP-2, MCP-5 mandatory
- **ACT-3+:** All 7 controls mandatory
- **ACT-4:** All 7 controls + CP.9 lineage token propagation through MCP delegation chains

**MITRE ATLAS:** AML.T0002, AML.T0005, AML.T0051
**OWASP LLM:** LLM05 (Supply Chain Vulnerabilities), LLM10 (Model Theft / Exfiltration)

> Full research foundation and implementation rationale: [Research Note 023 — MCP Server Security Profile](../research/023_mcp-server-security-profile.md)

---

---

<a id="cp6"></a>
## CP.6 — AI Incident Feedback Loop Integration

**What it governs:** How external AI incident intelligence flows back into your governance controls on a defined cadence.

**Core requirements:**
- Quarterly review of AIID agentic incident reports
- 30-day Incident-Informed Control Review (IICR) triggered when a new relevant AIID incident is published
- Internal Agentic Incident Registry for organizational lessons-learned

**Why it matters:** The threat landscape changes faster than annual governance reviews. CP.6 creates a structured forcing function that keeps controls current without waiting for the next major incident inside your own organization.

---

<a id="cp7"></a>
## CP.7 — Deception & Active Defense Layer

**What it governs:** AI-specific active defense assets that detect and study attackers before they succeed.

**Control components:**
- **Canary documents in RAG corpora:** Documents that should never appear in legitimate agent outputs; retrieval triggers an immediate alert
- **Honeypot tool endpoints:** Tools that should never be called in normal operation; invocation indicates adversarial probing or tool squatting
- **Fake credential traps in agent memory:** Credentials that trigger alerts when exfiltrated

**Why it matters:** Every other AI governance framework is purely defensive — detect and block. CP.7 is the only control that tells you to deceive and catch. It is the only deception-class control in any current AI governance framework.

---

<a id="cp8"></a>
## CP.8 — Catastrophic Risk Threshold Controls

**What it governs:** Behavioral indicators that trigger emergency agent suspension regardless of business continuity impact.

**Example catastrophic paths:**
- (a) Agentic ransomware or malicious operator agents abusing NHI and orchestration to execute full kill-chains with legitimate credentials
- (b) Protocol-layer supply chain compromise of widely deployed A2A or MCP servers
- (c) Persistent cognitive or bias failures that materially impact safety-critical or financial decisions

**Governance requirement:** CRT documentation is mandatory before any ACT-3 or ACT-4 deployment approval. A CRT review board must hold authority to permanently decommission agents exhibiting threshold-triggering behavior.

---

<a id="cp9"></a>
## CP.9 — Agent Replication Governance (ARG)

![First in Field - Unified Security Control Model](https://img.shields.io/badge/First_in_Field-No_other_framework_has_this_standard-cc6600?style=flat-square)

![First in Field - Cross-Layer Enforcement Requirement](https://img.shields.io/badge/First_in_Field-No_other_framework_requires_this-cc6600?style=flat-square)

**What it governs:** The first formal governance standard for agent replication — the moment one agent can clone itself, four core security assumptions simultaneously collapse.

**The four collapsing assumptions:**
1. One identity per actor
2. One permission set per identity
3. One execution context per session
4. One audit trail per actor

All four fail at once, at machine speed. NIST, ISO, OWASP, and enterprise IAM have zero standards for this.

**CP.9 requires:**
- Replication authority must be explicitly declared in deployment manifests and enforced at the gateway layer
- Every spawned sub-agent receives a new ephemeral credential with scope narrowing at every delegation hop (per research/014 Control Spec 4)
- A cryptographic lineage token travels with every agent, encoding parent DID, chain ID, delegation depth, and TTL
- ACT-3 deployments: maximum 2 delegation hops; ACT-4: maximum 3 hops
- Kill switch severs the full delegation tree at the gateway and revokes all descendant credentials within 500ms
- A2.4 Dynamic Agent State Inventory is extended with `replication_lineage` field; reconciliation minimum every 60 minutes for ACT-3/ACT-4

**Why it matters:** One agent becoming a thousand identities before your SIEM fires a single alert is not theoretical. It is the natural behavior of production orchestrator agents with no replication governance. CP.9 is the spec that prevents this.

---

<a id="cp10"></a>
## CP.10 — The HEAR Doctrine (Human Ethical Agent of Record)

![First in Field - Unified Security Control Model](https://img.shields.io/badge/First_in_Field-No_other_framework_has_this_standard-cc6600?style=flat-square)

![First in Field - Cross-Layer Enforcement Requirement](https://img.shields.io/badge/First_in_Field-No_other_framework_requires_this-cc6600?style=flat-square)

**What it governs:** The requirement that every ACT-3 and ACT-4 deployment has a named Human Ethical Agent of Record with cryptographic signing authority and unilateral kill-switch capability.

**The HEAR is not:**
- A governance committee
- An approval workflow
- An incident response team

**The HEAR is:** A specific named individual who holds a cryptographic private key, can be reached in real time, and has the unilateral authority to stop any autonomous agent deployment in their designated boundary at any time, for any reason, without prior approval.

**Class-H Action Protocol:** Any irreversible, financially material, security-modifying, or cross-organizational action requires:
1. Agent pauses execution
2. Agent presents plain-language semantic consequence to the HEAR (not the technical parameters — the real-world effect)
3. HEAR signs the authorization with their registered private key
4. Agent verifies the signature before proceeding
5. Authorization logged to A2.5 before execution

**Fail-closed requirement:** If the HEAR is unreachable or the signing infrastructure fails, Class-H actions are blocked. No automatic approval path exists for any Class-H category.

**Compliance mappings:**
- EU AI Act Articles 9 and 14 (human oversight for high-risk AI)
- SEC Cybersecurity Disclosure accountability requirements
- SOC 2 CC.7.4
- GDPR Article 22 automated decision safeguards
- NIST AI RMF GOVERN function

---

## 📊 Cross-Pillar GRC Mapping

| Framework | CP Control | Requirement Satisfied |
| :--- | :--- | :--- |
| EU AI Act Art. 9 | CP.10 HEAR | Designated responsible person for high-risk AI |
| EU AI Act Art. 14 | CP.10 HEAR | Human oversight intervention capability |
| NIST AI RMF GOVERN | CP.3, CP.4, CP.10 | Organizational accountability for AI risk |
| SEC Cyber Disclosure | CP.3, CP.4, CP.10 | Board-level AI governance evidence |
| SOC 2 CC.7.4 | CP.10 HEAR | Incident response documentation |
| GDPR Art. 22 | CP.10 HEAR | Automated decision safeguards |
| ISO/IEC 42001 | CP.1-CP.8 | AI management system governance |
| OWASP Agentic Top 10 | CP.9 | ASI03 Identity Abuse (first framework to address) |
| OWASP Agentic Top 10 | CP.10 | ASI09 Human-Agent Trust Exploitation (first framework to address) |
| OWASP AIVSS v0.8 | CP.3, CP.2 | ACT tier scoring integration |

---

## 🚀 Getting Started with Cross-Pillar Governance

**For immediate value, implement in this order:**

1. **Classify all deployed agents by ACT tier** (CP.3) — this takes less than a day and unlocks every subsequent governance conversation
2. **Assign owner_of_record to every agent** (CP.4, A2.4) — agents without an owner cannot be approved for production at ACT-3/ACT-4
3. **Designate a HEAR for every ACT-3/ACT-4 deployment** (CP.10) — register in A2.4 before the next security review
4. **Define Catastrophic Risk Thresholds** (CP.8) — required condition for any new ACT-3/ACT-4 deployment approval
5. **Audit replication capability** (CP.9) — if any agent can spawn sub-agents, the replication governance spec applies now

> Full implementation guidance, including the 30-Day Roadmap from greenfield to full v3.0 compliance, is in the [AI SAFE² v3.0 Implementation Toolkit](https://cyberstrategyinstitute.com/ai-safe2/).

---

<div align="center">

<a href="https://cyberstrategyinstitute.com/ai-safe2/">
  <img src="https://img.shields.io/badge/GET_THE_v3.0_TOOLKIT_($97)-cc6600?style=for-the-badge&logo=rocket&logoColor=white" alt="AI SAFE v3.0 Implementation Toolkit Download" />
</a>

<p><i>Full CP.1-CP.10 specifications, implementation requirements, compliance evidence templates, and ACT tier assignment tools.</i></p>

</div>

---

## 🔗 Navigation

| | | |
| :--- | :--- | :--- |
| [Main README](../README.md) | [All Five Pillars](#) | **Cross-Pillar Governance** |
| [Pillar 1](../01-sanitize-isolate/README.md) | [Pillar 2](../02-audit-inventory/README.md) | [Pillar 3](../03-fail-safe-recovery/README.md) |
| [Pillar 4](../04-engage-monitor/README.md) | [Pillar 5](../05-evolve-educate/README.md) | [AISM Layer](../AISM/) |

→ [Interactive Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)
→ [Research Notes 001-014](../research/)

---

*Powered by [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
