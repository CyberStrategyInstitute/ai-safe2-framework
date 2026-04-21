# Research Note 6: NHI and Orchestration — The Board and Regulator View

**Series:** AI SAFE2 v3.0 Research Foundation  
**Topic:** ACT Tiers and CP.4 as Evidence of Agentic Control Plane Governance  
**Controls Supported:** CP.3, CP.4, A2.4  
**Audience:** CISOs, boards of directors, compliance officers, regulators  
**Date:** April 2026

---

## 1. Purpose

This research note is structured as a CISO briefing memo: it explains why Non-Human Identities and agent orchestration have become a board-level governance concern, and how AI SAFE2 v3.0's ACT capability tiers and CP.4 Agentic Control Plane controls provide the governance evidence structure boards and regulators need to assess an organization's AI governance posture.

This note is intentionally written for a non-technical audience. The technical foundations are covered in the preceding research notes; this note focuses on governance implications.

---

## 2. Why This Is Now a Board-Level Issue

### 2.1 The Scale Shift

Two years ago, AI in the enterprise meant: an AI assistant that could generate text, analyze documents, or answer questions. A human reviewed the output before anything happened. The AI had no autonomous authority.

Today, AI in the enterprise increasingly means: AI agents that take actions — send emails, create records, modify configurations, make financial transactions, query databases, invoke APIs — without human review of each individual action. The AI has autonomous authority over a growing set of business operations.

This is not a future risk. It is the current state of production agentic deployments in AWS Bedrock, Azure AI Foundry, Salesforce Agentforce, ServiceNow, and no-code automation platforms like n8n and Power Automate. Organizations that have not yet deployed agentic AI are planning to. Organizations that have deployed agentic AI are expanding those deployments.

### 2.2 The Accountability Gap

When an AI agent takes an action autonomously, three accountability questions immediately arise:

1. **Who authorized this agent to take this action?** (Authorization accountability)
2. **Who is responsible for monitoring this agent's behavior?** (Operational accountability)
3. **What are the limits of this agent's authority, and how are those limits enforced?** (Governance accountability)

In most current agentic deployments, none of these questions have clear answers. Agents are provisioned with service account credentials (Non-Human Identities) that have broad permissions. Agents run continuously without a named owner accountable for their behavior. The limits of an agent's authority are informally specified in a system prompt, not formally enforced by a governance control.

This is an accountability gap with material risk implications: when an agent causes harm — financial loss, data breach, regulatory violation, safety incident — the organization cannot clearly answer who authorized the action, who was monitoring the agent, or what governance control should have prevented the harm.

### 2.3 Why Regulators Are Beginning to Ask About This

Regulatory attention to AI governance is increasing across multiple domains:

- **Financial services**: Regulators are beginning to require evidence of AI model risk management for deployed AI systems, including agentic systems making credit, fraud, or transaction decisions
- **Healthcare**: HIPAA enforcement is extending to AI systems with access to PHI, including agentic systems that process patient data autonomously
- **EU AI Act**: Article 9 requires risk management systems for high-risk AI systems; Article 12 requires logging and audit trails for high-risk AI decisions — requirements that directly implicate agentic AI governance
- **SOC 2 Type II**: Auditors are increasingly asking about AI system governance controls as part of availability, confidentiality, and processing integrity criteria

The common thread: regulators and auditors want to know that organizations can identify what AI systems are deployed, what authority they have, who is accountable for them, and what governance controls are in place.

---

## 3. NHI and Orchestration as the Primary AI Control Plane

### 3.1 What "Control Plane" Means in This Context

In network infrastructure, the "control plane" is the infrastructure that controls how traffic flows — routing tables, access control policies, and management interfaces. The "data plane" is the infrastructure that carries the traffic. Security teams govern the control plane because whoever controls the control plane controls the network.

In agentic AI deployments, the equivalent control plane is:
- **Non-Human Identities**: The service account credentials that grant AI agents authority to act within organizational systems
- **Orchestration infrastructure**: The systems (LangGraph, n8n, Power Automate, Bedrock multi-agent collaboration, Azure Copilot Studio) that determine which agents run, what tasks they execute, and with what authority

Whoever controls the NHI credentials and orchestration infrastructure controls the autonomous AI systems. This is the AI control plane.

### 3.2 The Current Governance Gap

In most organizations, NHI governance and AI governance are managed by different teams using different processes:

- **NHI governance** (if it exists) is typically owned by identity and access management teams, focused on service account lifecycle management and least privilege
- **AI governance** is typically owned by data science, AI CoE, or risk management teams, focused on model performance, bias, and responsible AI

Neither team typically governs the intersection: the AI agents that operate as NHIs using orchestration infrastructure. This intersection is the AI control plane — and it is frequently ungoverned.

---

## 4. How AI SAFE2 v3.0 Provides the Governance Evidence Structure

### 4.1 The ACT Capability Tier System (CP.3)

The ACT tier system provides the most important single governance artifact for board and regulator reporting: a risk-proportionate classification of every deployed AI agent.

Boards and audit committees need to be able to ask: "What AI agents do we have, how autonomous are they, and what controls govern each tier?" The ACT system answers this question:

| What the Board Needs to Know | How ACT Tiers Provide the Answer |
|---|---|
| How many AI agents are deployed? | Count of agents in A2.4 registry, classified by ACT tier |
| Which agents have autonomous authority? | ACT-3 and ACT-4 agents — require the highest governance controls |
| What are the limits of each agent's authority? | Defined by ACT tier and owner_of_record in A2.4 inventory |
| What controls govern the highest-autonomy agents? | CP.4, F3.2, M4.4, owner_of_record requirements — all required for ACT-3+ |

A board-level AI risk report should include a simple ACT tier dashboard: how many agents at each tier, what is the aggregate AAF risk score across the portfolio, and what controls are confirmed as implemented at each tier.

### 4.2 The Agentic Control Plane Framework (CP.4)

CP.4 provides the governance evidence framework for the AI control plane itself. It maps controls to three layers:

**Authorization layer**: Who authorized each agent, what authority it has, and what identity it operates under. Evidence: A2.4 registry with owner_of_record and control_plane_id; P1.T2.2 NHI least privilege documentation; P2.T2.1 NHI registry with lifecycle records.

**Orchestration layer**: What controls govern the orchestration infrastructure — how tasks are assigned to agents, how delegations are scoped, and how the orchestration topology is documented. Evidence: A2.4 dynamic agent state inventory; CP.3 ACT tier assignments; F3.2 recursion limits per ACT tier.

**Runtime behavioral trust layer**: What controls continuously validate that agents are behaving within their authorized scope. Evidence: M4.4 through M4.8 monitoring controls; F3.4 behavioral drift baselines; E5.1 continuous adversarial evaluation with ASR scores.

A CISO presenting to a board or regulator can use the three-layer CP.4 structure as the framework for explaining how the organization governs its AI control plane. Each layer maps to specific controls with specific evidence artifacts.

### 4.3 The `owner_of_record` Requirement (A2.4)

The `owner_of_record` field in A2.4 is the most operationally important single requirement for board governance accountability. It specifies that every agent and orchestration flow must have a named human, team, or business unit accountable for its behavior.

This answers the accountability gap described in Section 2.2:
- **Who authorized this agent?** The owner_of_record approved the agent's deployment
- **Who is responsible for monitoring?** The owner_of_record is the primary escalation point for behavioral anomalies
- **Who is accountable when the agent causes harm?** The owner_of_record and their management chain

The A2.4 requirement that "any agent or flow without an owner MUST be escalated as a governance failure and resolved before promotion to production" is the enforcement mechanism. It prevents the default state — ungoverned agents accumulating in production — by making the absence of an owner a governance blocker.

---

## 5. Board-Level Metrics for Agentic AI Governance

Boards and audit committees should request the following metrics from management as evidence of Agentic Control Plane governance:

### 5.1 Inventory Metrics

| Metric | What It Measures | Target |
|---|---|---|
| % of deployed agents in A2.4 registry | Coverage of agent inventory control | 100% |
| % of agents with assigned owner_of_record | Accountability coverage | 100% |
| Number of ACT-3 and ACT-4 agents | Scope of highest-risk deployments | Known and bounded |
| % of ACT-3+ agents with completed AMLTM | CP.2 compliance for autonomous agents | 100% |

### 5.2 Risk Metrics

| Metric | What It Measures | Target |
|---|---|---|
| Aggregate AAF score across agent portfolio | Portfolio-level agentic risk | Tracked and trending |
| Number of agents with AAF > 7.0 (High) | Scope of high-amplification deployments | Known and governed |
| Average Pillar Score across ACT-3+ agents | SAFE2 implementation maturity | >75 (target: >85) |
| Combined Risk Score for top-5 highest-risk agents | Individual agent risk posture | Reviewed quarterly |

### 5.3 Operational Metrics

| Metric | What It Measures | Target |
|---|---|---|
| Average time to detect behavioral anomaly (M4.4, M4.6) | Detection effectiveness | <24 hours for Critical alerts |
| Number of CP.8 CRT threshold events | Catastrophic risk proximity | Zero; any event = immediate escalation |
| % of adversarial evaluation cycles meeting coverage requirements (E5.1) | Continuous evaluation effectiveness | 100% |
| Number of agentic incidents by temporal profile (CP.2) | Attack pattern visibility | Tracked; trended quarterly |

### 5.4 Compliance Metrics

| Metric | What It Measures | Target |
|---|---|---|
| SAFE2 v3.0 Pillar Score (1-100 per pillar) | Framework control implementation | >75 per pillar |
| Number of Critical controls not implemented for ACT-3+ agents | Governance gap severity | Zero |
| Protocol-layer supply chain assessments completed (CP.5) | Protocol governance coverage | 100% of production protocols |

---

## 6. Regulatory Mapping

### 6.1 EU AI Act Alignment

| EU AI Act Requirement | SAFE2 v3.0 Evidence |
|---|---|
| Article 9: Risk management system | CP.3 ACT tiers; A2.4 AAF scores; CP.8 CRT thresholds |
| Article 12: Logging and traceability | A2.5 semantic execution trace logging; P2.T3.1 real-time activity logging |
| Article 13: Transparency | CP.4 Agentic Control Plane documentation; A2.4 agent registry |
| Article 17: Quality management | E5.1 continuous adversarial evaluation; CP.6 incident feedback loop |

### 6.2 NIST AI RMF Alignment

| NIST AI RMF Function | SAFE2 v3.0 Evidence |
|---|---|
| GOVERN | CP.3, CP.4, A2.4 (owner_of_record), CP.8 |
| MAP | A2.4, A2.3 (lineage), P2.T4 (inventory) |
| MEASURE | Risk scoring formula (CVSS + Pillar + AAF), E5.1 (continuous evaluation) |
| MANAGE | F3.2, F3.5, CP.8, CP.6 (incident feedback) |

### 6.3 ISO 42001 Alignment

AI SAFE2 v3.0 maintains 100% ISO 42001 coverage. For agentic governance specifically:
- Section 8.1 (Operational planning and control): CP.3 ACT tiers provide the risk-proportionate control structure
- Section 8.4 (AI system management): A2.3 (lineage), A2.4 (inventory), A2.5 (trace logging) provide the documentation required
- Section 9.1 (Monitoring and measurement): M4.4-M4.8 provide the monitoring infrastructure; E5.1 provides continuous evaluation evidence

---

## 7. References

- CSA Agentic Control Plane framework — control plane governance concept.
- CSA CSAI Foundation — NHI and AI governance intersection.
- OWASP AIVSS v0.8 — GOVERN function alignment.
- NIST AI RMF — function mapping to SAFE2 v3.0.
- EU AI Act — Article 9, 12, 13, 17 requirements.
- International AI Safety Report 2026 — systemic AI risk categories.
- AI SAFE2 v3.0 Framework, Sections CP.3, CP.4, A2.4, CP.8.

---

*This research note is part of the AI SAFE2 v3.0 research foundation series. It is written for CISO and board-level audiences. Cyber Strategy Institute, 2026.*
