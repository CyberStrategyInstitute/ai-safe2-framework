# AI SAFE² Framework Evolution History

This document outlines the strategic evolution of the AI SAFE² framework, detailing the transition from a conceptual foundation to a production-hardened agentic governance engine.

---

## Version History

| Version | Released | Controls | Frameworks | Jump To |
| :--- | :--- | :--- | :--- | :--- |
| **v3.0** | April 2026 | 161 (151 pillar + 10 CP) | 32 | [v3.0](#v30) |
| v2.1 | November 2025 | 128 | 14 | [v2.1](#v21) |
| v2.0 | October 2025 | 99 | Core | [v2.0](#v20) |
| v1.0 | June 2025 | 10 | — | [v1.0](#v10) |

---

<a id="v30"></a>
## 🔥 Version 3.0: Swarm Governance & Production Evidence Edition (Current)

**Released:** April 2026
**Core Concept:** "The Governance OS for Autonomous AI."

Version 3.0 is the shift from framework coverage to engineering certainty. Where v2.1 defined what agentic governance should look like, v3.0 defines what it must enforce — grounded entirely in validated production red-team findings from AWS Bedrock, Azure AI Foundry, and n8n deployments. Every new control traces directly to a failure mode found in the field, not a theoretical risk.

The headline addition is not a single control but an architectural layer: the Cross-Pillar Governance OS (CP.1 through CP.10), which defines the authority structures, accountability primitives, and risk scoring mechanisms that operate across all five pillars simultaneously. This is the layer that was missing. Two controls in this layer are first-in-field with no equivalent in any other governance framework.

**Control count:** 151 pillar controls (128 from v2.1 + 23 new) plus 10 cross-pillar governance controls = **161 total controls**

### What Changed and Why

**The attack surface changed and the frameworks did not catch up.**
CVE-2026-25049 (n8n sandbox escape series) is being actively exploited in production deployments built entirely on no-code platforms. AWS Bedrock Guardrail poisoning via the UpdateGuardrail API is a confirmed attack path that standard CloudTrail monitoring does not flag. S1.7 and M4.8 exist because of these specific findings.

**Agent replication had no governance standard anywhere.**
The moment an agent can clone itself, four IAM assumptions collapse simultaneously: one identity, one permission set, one execution context, one audit trail. All at machine speed. NIST, ISO, OWASP, and enterprise IAM had zero standards for this. CP.9 Agent Replication Governance is the first.

**60 percent of organizations cannot stop a misbehaving agent.**
Not because they lack the will — because nobody had defined who holds the authority and the cryptographic capability to act when it matters. CP.10 HEAR Doctrine establishes the Human Ethical Agent of Record: a named individual with a signing key, real-time interrupt capability, and unilateral kill-switch authority.

**Risk scoring for agentic AI required a new formula.**
A CVSS 7.5 vulnerability in a read-only chatbot is a different risk than the same vulnerability in an ACT-4 orchestrator with cross-session memory and enterprise tool access. OWASP AIVSS v0.8 defined the Agentic Amplification Factor to capture this. AI SAFE² v3.0 is the first framework to integrate AAF into a GRC risk formula: `CVSS + (100 - Pillar Score) / 10 + (AAF / 10)`.

### Key Changes by Pillar

- **Pillar 1 (Sanitize & Isolate):** Six new controls address the indirect injection surface (every non-prompt input the agent reads, not just user input), semantic isolation between trusted instructions and untrusted content, adversarial fuzzing integrated into CI/CD pipelines, memory governance boundaries that govern every write to persistent agent memory, cognitive injection detection for multi-turn conditioning and role confusion, and the first dedicated governance standard for no-code platform security.

- **Pillar 2 (Audit & Inventory):** Four new controls add cryptographic model lineage provenance from base model through every fine-tuning stage, a real-time dynamic agent state inventory with mandatory owner_of_record fields, semantic execution trace logging that captures the full reasoning chain and every memory operation to an append-only store, and hash-verified RAG corpus diff tracking that correlates behavioral changes to retrieval layer changes automatically.

- **Pillar 3 (Fail-Safe & Recovery):** Four new controls add a hard recursion limit governor enforced at the API gateway layer (not in the system prompt), a decentralized swarm quorum abort mechanism that stops a coordinated multi-agent effort without a centralized kill signal, behavioral drift baselines with automated rollback when thresholds are exceeded, and multi-agent cascade containment that limits the blast radius of failures in pipeline architectures.

- **Pillar 4 (Engage & Monitor):** Five new controls add a continuous adversarial behavior detection pipeline that probes deployed agents in production, tool-misuse detection that establishes invocation baselines and catches tool squatting, emergent behavior anomaly detection that classifies new agent capabilities as a security signal, a unified jailbreak and injection telemetry layer with technique classification, and cloud AI platform-specific monitoring for Bedrock and Azure AI Foundry attack paths that standard monitoring misses.

- **Pillar 5 (Evolve & Educate):** Four new controls define mandatory evaluation gates triggered by model updates and system changes, a structured governance process for emergent agent capabilities with tiered review, a validated reference implementation library for all AI SAFE² controls with platform-specific variants, and a red-team artifact repository with a defined schema that turns every finding into a permanent reusable test case.

- **Cross-Pillar Governance Layer (CP.1-CP.10):** The governance OS defines agent failure mode taxonomy with mandatory cognitive and temporal tagging, adversarial ML threat model integration with temporal profiles, ACT Capability Tiers 1-4 that scale mandatory controls with agent autonomy, the Agentic Control Plane as a board-visible governance concept, platform-specific security profiles including protocol-layer supply chain, AIID incident feedback integration with a 30-day update cadence, a deception and active defense layer (first in any AI governance framework), catastrophic risk threshold controls required as a condition of ACT-3/ACT-4 deployment approval, Agent Replication Governance (first in field), and the HEAR Doctrine (first in field).

### Compliance Coverage: 14 Frameworks (v2.1) to 32 Frameworks (v3.0)

v3.0 doubles the compliance coverage. The 14 frameworks from v2.1 are all retained and expanded. 18 new frameworks are added.

**Retained from v2.1 — expanded in v3.0:**

| Standard | v2.1 | v3.0 | What Expanded |
| :--- | :--- | :--- | :--- |
| NIST AI RMF | 100% | 100% | CP.3, CP.4, CP.8 now map to GOVERN; E5.1 maps to MEASURE |
| ISO/IEC 42001 | 100% | 100% | CP.6 now maps to Sec 9 continuous improvement |
| MIT AI Risk Repository v4 | 100% | 100% | Catastrophic risk pathways (CP.8), CBRN risks |
| OWASP Top 10 LLM | 100% | 100% | New agentic variants of LLM01-LLM10 covered |
| MITRE ATLAS | 98% | **100%** | All 14 new agent-specific techniques (Oct 2025) now mapped |
| Google SAIF | 95% | 97% | Swarm and NHI governance gaps further closed |
| CSETv1 Harm | 92% | 92% | Retained |
| SOC 2 Type II | Aligned | Aligned+ | CC.7.4 now maps to CP.10 HEAR; C.1 maps to S1.5 |
| ISO 27001:2022 | Aligned | Aligned+ | A.8.8 vuln mgmt maps to M4.8; A.12.4 maps to A2.5 |
| NIST CSF | Aligned | Aligned+ | GOVERN function now maps to CP.x; CSF 2.0 updated |
| HIPAA | Aligned | Aligned+ | S1.5 cross-session PHI memory; P3.T6 disaster recovery |
| GDPR | Aligned | Aligned+ | Art.22 automated decisions maps to CP.10; Art.33 maps to CP.6 |
| CVE / CVSS | Integrated | Integrated+ | Formula updated: `CVSS + (100 - Pillar Score) / 10 + (AAF / 10)` |
| Zero Trust | Native | Native | NHI lifecycle deepened via CP.4 control plane governance |

**New in v3.0 — 18 additions:**

*AI-Specific (10 new):*

| Standard | Coverage | Key Mapping |
| :--- | :--- | :--- |
| OWASP AIVSS v0.8 | 100% | All 10 core agentic risks + AAF scoring formula integrated — first framework to do this |
| OWASP Agentic Top 10 (ASI) | 100% | ASI01-ASI10; CP.9 addresses ASI03 Identity Abuse; CP.10 addresses ASI09 |
| CSA Agentic Control Plane | 85% | CP.4 covers identity, authorization, orchestration, and runtime trust |
| CSA Zero Trust for LLMs | 90% | S1.3 micro-perimeter per agent; CP.4 policy-as-code; A2.5 trace logging |
| MAESTRO (CSA 7-Layer) | 95% | All 7 layers covered via pillars and CP controls |
| Arcanum PI Taxonomy | 95% | Evasion techniques (P1.T1.2), indirect surfaces (P1.T1.10), cognitive layer (S1.6) |
| AIDEFEND (7 Tactics) | 90% | Deceive tactic (CP.7), Evict (F3.5), Harden shift-left (S1.4) |
| AIID Agentic Incidents | 90% | CP.6 incident feedback loop; M4.8 platform monitoring |
| EU AI Act (2024) | Aligned | High-risk AI: CP.3 / GPAI: A2.3 / Human oversight: CP.10 HEAR |
| International AI Safety Report 2026 | Aligned | Catastrophic risk: CP.8 / Loss of control: F3.2-F3.5 / Evaluation: E5.1-E5.4 |

*Enterprise (8 new):*

| Standard | Coverage | Key Mapping |
| :--- | :--- | :--- |
| PCI-DSS v4.0 | Aligned+ | P1.T1.5 PAN masking; P1.T2 network segmentation Req 1.3; M4.8 cloud AI Req 6.4 |
| NIST SP 800-53 Rev 5 | Aligned+ | AC: P1.T2, CP.4 / AU: P2.T3, A2.5 / IR: CP.6, F3.x / RA: CP.2, CP.3 |
| FedRAMP | Aligned+ | High baseline: full ACT-3/ACT-4 controls; S1.7 for no-code interconnections |
| CMMC 2.0 | Aligned+ | Level 1: P1-P2 / Level 2: P1-P5 + CP.3-CP.4 / Level 3: E5.x + CP.8 |
| CIS Controls v8 | Aligned+ | CIS-1: A2.4 / CIS-6: CP.4 / CIS-8: A2.5 / CIS-17: CP.6 |
| CCPA / CPRA | Aligned+ | P1.T1.5 PII in AI inputs; S1.5 cross-session memory; M4.6 decision bias |
| SEC Cyber Disclosure | Aligned+ | Material incident: CP.6 IICR; Board accountability: CP.3, CP.4, CP.10 |
| DORA | Aligned+ | ICT risk: CP.2 / Incident reporting: CP.6 / Resilience testing: E5.1 |

> **Analogy:** If v2.1 was the mission control center managing a fleet of autonomous drones, v3.0 is the moment mission control realized that the drones could spawn their own drones — and built the authorization layer, the lineage tracking, and the named human with the cryptographic key to ground the entire fleet, including every drone spawned by every other drone, in under 500 milliseconds.

---

<a id="v21"></a>
## 🚀 Version 2.1: Advanced Agentic & Distributed AI Edition

**Released:** November 2025
**Core Concept:** "Mission Control for Autonomous Drones."

Version 2.1 transforms AI SAFE² into an Agentic GRC + Security blueprint. It integrates 30+ specialized "Gap Fillers" specifically designed to address swarm intelligence, Non-Human Identity (NHI) governance, and advanced memory security.

### Key Changes by Pillar

- **Pillar 1 (Sanitize & Isolate):** Now includes OpenSSF Model Signing (OMS), real-time secret scanning (GitGuardian), and mitigation for memory attacks (AgentPoison). Isolation moves to Multi-Agent Boundary Enforcement and P2P trust scoring.
- **Pillar 2 (Audit & Inventory):** Enhanced for Decision Traceability (reasoning chains) and SHA-256 state verification. Inventory now mandates Swarm Topology Maps and automated NHI Registries.
- **Pillar 3 (Fail-Safe & Recovery):** Introduces Distributed Kill Switches for swarms and specific playbooks for context injection attacks. Recovery expands to HSM-integrated credential recovery.
- **Pillar 4 (Engage & Monitor):** Formalizes human oversight for consensus failures and Just-In-Time (JIT) privilege elevation for agents. Monitoring now detects "ghost tokens" and poisoned vector embeddings.
- **Pillar 5 (Evolve & Educate):** Focuses on agile consensus algorithms and updates to OMS specifications. Training now includes Swarm Manager Certification.

### Compliance Coverage: 14 Frameworks

NIST AI RMF (100%), ISO/IEC 42001 (100%), MIT AI Risk Repository (100%), OWASP Top 10 LLM (100%), MITRE ATLAS (98%), Google SAIF (95%), CSETv1 Harm (92%), SOC 2 Type II (Aligned), ISO 27001:2022 (Aligned), NIST CSF (Aligned), HIPAA (Aligned), GDPR (Aligned), CVE/CVSS (Integrated: `CVSS + (100 - Pillar Score) / 10`), Zero Trust (Native).

> **Analogy:** If v1.0 was a propeller plane, v2.1 is the advanced mission control center required to manage an entire fleet of autonomous drones, ensuring each drone (agent) has the right credentials, stays within its flight path, and can be instantly grounded if its internal logic is compromised.

---

<a id="v20"></a>
## 🏢 Version 2.0: The Enterprise Operational Standard

**Released:** October 2025
**Core Concept:** "High-Tech Building Security."

The shift from v1.0 to v2.0 represented a move from a conceptual model to a granular, enterprise-grade operational framework. It expanded the 5 pillars into 99 detailed subtopics and integrated with NIST, OWASP, and MITRE ATLAS.

### Key Upgrades

- **Architecture:** Introduced the Five-Layer Architecture Model covering the entire AI stack.
- **Compliance:** Achieved 100% coverage of OWASP Top 10 for LLM and NIST AI RMF.
- **Risk Scoring:** Introduced the Combined Risk Score formula (Vulnerability + Control Effectiveness).

### Evolution by Pillar

- **P1:** Expanded to comprehensive input validation (schema enforcement, toxic content) and detailed boundary enforcement.
- **P2:** Shifted to real-time activity logging, bias monitoring, and automated SBOM generation.
- **P3:** Transitioned to advanced resilience controls (circuit breakers) and formal RTO/RPO management.
- **P4:** Formalized "human-in-the-loop" into structured oversight and real-time SIEM integration.
- **P5:** Transformed training into a culture-building program with specialized operator education.

---

<a id="v10"></a>
## 🏛️ Version 1.0: The Foundational Structure

**Released:** June 2025
**Core Concept:** "The Blueprint."

The original conceptual foundation that established the **S-A-F-E-E** methodology.

- Provided the core philosophy of securing AI.
- Established the 5-Pillar structure.
- Identified the top 10 core topics for AI security.

---

## 📊 Summary of Transitions

| Transition | Shift | Controls | Frameworks | Core Metaphor |
| :--- | :--- | :--- | :--- | :--- |
| **v1.0 to v2.0** | Concept to enterprise operations | 10 to 99 | — to core | Blueprint to building |
| **v2.0 to v2.1** | Generic to agentic-native | 99 to 128 | Core to 14 | Building to mission control |
| **v2.1 to v3.0** | Coverage to engineering certainty | 128 to 161 | 14 to 32 | Mission control to governance OS |

The framework has moved from **securing AI as a tool** (v1.0) to **governing AI as an autonomous workforce** (v2.1) to **enforcing a formal governance contract over AI systems that can replicate, delegate, and act irreversibly** (v3.0). Each version answered the most urgent question its moment raised. v3.0 answers the question every organization running autonomous agents in production is about to face: who has the authority to stop this, and can they exercise it fast enough to matter.

---

*Managed by [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
