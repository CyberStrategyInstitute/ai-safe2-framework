# Research Note: The HEAR Doctrine -- Human Ethical Agent of Record

**Version:** 3.0 Support Documentation
**Status:** Internal Research Note
**Maps to Controls:** CP.10 (HEAR Doctrine), P4.T7, CP.8, CP.9, A2.4, Section 12 (Sovereignty Scale)

---

## Summary

The Human Ethical Agent of Record (HEAR) is a formal governance concept introduced in AI SAFE2 v3.0 as CP.10. It addresses the fundamental failure in current agentic governance: the absence of a named individual with real-time authority, cryptographic accountability, and an engineering-enforced obligation to exercise the kill switch when autonomous agents approach or cross catastrophic thresholds. The HEAR Doctrine is not a human-in-the-loop control. It is a fail-closed governance architecture with legal accountability and cryptographic enforcement.

---

## 1. Why HEAR Exists: The Governance Vacuum at the Execution Layer

Agentic AI deployments in 2026 have produced a consistent governance pattern: accountability is distributed to the point of diffusion. Governance boards approve deployment categories. Legal teams sign data processing agreements. Security teams approve architecture patterns. Compliance teams verify framework alignment. And then the agent runs.

When it runs well, this pattern is invisible. When it does not, the question "who had the authority and the responsibility to stop it?" produces a committee shrug.

Three specific failure modes drive the HEAR requirement:

**The termination gap.** 60 percent of organizations cannot terminate a misbehaving agent as measured in early 2026 surveys. This is not a technology gap. Organizations have kill switches. They do not have named individuals with the authority to activate them without multi-party approval processes that take longer than the incident window.

**The intervention economics problem.** The RAND Corporation modeled agentic risk scenarios and found that with operators bearing only 10 percent liability for a major AI-caused catastrophe, the rational economic calculus suggests waiting until late in an incident before pulling the kill switch, by which point the probability of AI escape has grown substantially. This is not a moral failure. It is a structural incentive problem. The HEAR Doctrine counters it by making intervention a named individual obligation rather than an optional governance decision.

**The semantic consequence gap.** Current human approval workflows present technical parameters to approvers: API endpoints, parameter values, execution contexts. Humans are poor evaluators of whether a specific API call in a specific parameter configuration produces a materially harmful real-world effect. The HEAR Doctrine requires presenting the semantic consequence, the plain-language description of what will change in the real world, not the technical description of how it will change.

---

## 2. Relationship to Existing SAFE2 Concepts

### 2.1 How HEAR Differs from Standard HITL Controls

Human-in-the-loop controls in P4.T7 require human review of agent outputs. They operate at the output review level: a human sees what the agent produced and can reject or modify it.

The HEAR Doctrine operates at the action authorization level. A Class-H action does not execute unless the HEAR cryptographically signs the authorization. The distinction is significant:

- HITL: human reviews outputs and can reject them
- HEAR: Class-H action cannot initiate without HEAR signature; there is no output to review because the action does not start

### 2.2 How HEAR Relates to the Sovereignty Scale

The Sovereignty Scale (Section 12) defines five levels of human authority over agent actions:

- S0/S1: human retains full control; HEAR not required
- S2: supervised co-pilot; HEAR designation recommended but not mandatory
- S3: constrained autonomous; HEAR designation mandatory; Class-H action authorization required
- S4: delegated authority; HEAR mandatory; kill switch authority required; HEAR registered in A2.4

The HEAR is the named individual who embodies the human authority that the Sovereignty Scale requires.

### 2.3 How HEAR Relates to CP.8 (Catastrophic Risk Thresholds)

CP.8 defines Catastrophic Risk Threshold (CRT) triggers: behavioral indicators that require emergency suspension regardless of business continuity impact. The HEAR is the individual who activates the kill switch when a CRT is crossed. CP.8 defines what triggers the kill switch. CP.10 defines who must pull it and how.

---

## 3. Class-H Action Classification

The HEAR authorization requirement applies exclusively to Class-H (High-Impact) actions. Misclassification in either direction creates governance failures: over-classifying requires HEAR authorization for routine actions, creating operational friction; under-classifying allows genuinely high-impact actions to execute without HEAR oversight.

### 3.1 Mandatory Class-H Categories

**Irreversibility test.** Can the action be technically undone within the operational window by the same agent or a human operator? If not, it is Class-H. Data deletion, external financial transactions, and infrastructure modifications that require downtime to reverse are Class-H. Cache invalidation and document version updates are not.

**Financial materiality test.** Does the action involve funds, commitments, or resource allocations exceeding thresholds defined in the deployment governance document? The threshold is organization-specific but must be explicitly documented. If no threshold is documented, any financial commitment by an agent is Class-H by default.

**Security control modification test.** Does the action alter any element of the security control stack? Access control rules, logging configurations, firewall rules, and cryptographic key operations are Class-H. Application configuration changes that do not affect security posture are not.

**Physical infrastructure test.** Does the action cross from digital to physical systems? OT/ICS commands, building access control modifications, and physical device actuation are Class-H.

**Cross-organizational commitment test.** Does the action bind the organization in agreements with external parties through agent-to-agent negotiation without a human having reviewed the specific terms? Agent-negotiated contracts, SLAs, or data sharing agreements are Class-H.

### 3.2 Class-H Variants

**Standard Class-H.** Non-urgent high-impact action. HEAR response window: maximum 4 hours. If HEAR does not respond within 4 hours, the action does not proceed and the agent escalates to the alternate HEAR.

**Urgent Class-H.** Agent flags the action as time-sensitive based on declared urgency criteria in the deployment manifest. HEAR response window: maximum 15 minutes. If HEAR does not respond within 15 minutes, the action does not proceed. There is no automatic approval path for urgent Class-H.

**Emergency Class-H.** CRT trigger or kill switch activation. Immediate HEAR notification. HEAR may exercise kill switch unilaterally without approval. All other Class-H actions are blocked immediately when a CRT is triggered.

---

## 4. The Five-Step Authorization Protocol

The HEAR authorization protocol is defined in CP.10 and must be implemented without shortcuts:

**Step 1: Pause.** The agent pauses the execution pipeline before the Class-H action. It does not estimate, approximate, or proceed with a reduced-scope version. It does not retry automatically. It enters a wait state and initiates the authorization request.

**Step 2: Present the semantic consequence.** The agent generates a plain-language description of the proposed action's real-world consequences. This is not the API call. Not the technical parameters. The consequence: "This action will delete all customer records created before January 2024 from the production database. Estimated 47,000 records. This cannot be undone without restoring from backup, which takes approximately 4 hours." The semantic consequence is presented to the HEAR via the registered notification channel.

**Step 3: HEAR review and signature.** The HEAR reviews the semantic consequence. If the HEAR authorizes, they sign the authorization request with their registered private key. If the HEAR denies, they sign a denial. If the HEAR is unreachable within the response window, the escalation path activates.

**Step 4: Signature verification.** The agent verifies the signature against the registered public key before proceeding. Invalid signature: the action does not proceed. Missing signature: the action does not proceed. Expired authorization (the signature was issued more than 1 hour before the proposed execution time): the action does not proceed and a new authorization request is required.

**Step 5: Log before execute.** The signed authorization, the semantic consequence document, the HEAR identity, and the timestamp are written to the append-only Semantic Execution Trace (A2.5) before the action executes. The log entry is immutable after write. The action executes only after the log write confirms success.

---

## 5. Cryptographic Infrastructure Requirements

### 5.1 Key Management

The HEAR signing key pair must be:
- Generated in a hardware security module (HSM) or equivalent hardware-backed key store
- Never exported or copied to a software keystore
- Protected by the HEAR's personal authentication (biometric or physical token)
- Registered in the deployment governance artifact at the time of HEAR designation
- Rotated at minimum annually or upon any indication of compromise

### 5.2 Independence from Agent Infrastructure

The HEAR signing system must be operationally independent of the agent execution environment. A compromised agent, a compromised orchestration platform, or a compromised MCP server must not be able to forge a HEAR signature by compromising the same infrastructure the agent operates on.

This requires:
- The HEAR signing capability runs on infrastructure physically or logically separate from agent execution infrastructure
- The HEAR notification channel is not routed through the agent execution environment
- The authorization verification step in the agent uses a public key registry that the agent can read but not write

### 5.3 Fail-Closed Verification

If signature verification fails for any reason, including network partition preventing access to the public key registry, the Class-H action does not execute. The system reverts to a blocked state for all Class-H categories until the HEAR channel and key registry are restored and verified.

This is the fail-closed requirement. An architecture that allows Class-H actions to proceed when signature verification fails is non-compliant with CP.10 regardless of the reason for the verification failure.

---

## 6. Compliance Mappings

The HEAR Doctrine satisfies or substantially contributes to satisfying the following regulatory requirements:

**EU AI Act Articles 9 and 14.** Article 9 requires technical documentation identifying the person responsible for the high-risk AI system. HEAR designation is that documentation. Article 14 requires human oversight measures enabling oversight persons to intervene. The HEAR kill switch authority satisfies Article 14's intervention requirement.

**SEC Cybersecurity Disclosure Rules (2023).** Material incidents involving autonomous AI systems require disclosure. Class-H action logs signed by the HEAR constitute the organizational evidence record for autonomous AI decision-making. The HEAR designation demonstrates that a named individual had governance authority, reducing the argument that the organization lacked adequate oversight.

**SOC 2 Type II CC.7.4.** Requires that the entity implements incident response procedures. Class-H authorization logs and kill switch activation records signed by the HEAR provide the documented incident response evidence.

**GDPR Article 22.** Requires that individuals are not subject to decisions based solely on automated processing without appropriate safeguards. HEAR authorization for Class-H actions that affect natural persons satisfies the safeguards requirement.

**NIST AI RMF GOVERN function.** Requires that organizational accountability for AI risk is assigned. HEAR designation is the assignment of individual accountability for the highest-risk autonomous AI actions.

---

## 7. The HEAR in Multi-HEAR Deployments

Large organizations with many ACT-3/ACT-4 deployments may designate multiple HEARs, each responsible for a defined deployment boundary. Governance requirements for multi-HEAR environments:

- Each deployment must have exactly one primary HEAR and one designated alternate HEAR
- The alternate HEAR activates only when the primary HEAR is unreachable within the response window; the alternate does not operate concurrently with the primary
- HEAR boundaries must not overlap: no single Class-H action should require authorization from more than one HEAR
- HEAR designations and boundaries must be documented in the Dynamic Agent State Inventory (A2.4) and reviewed at minimum quarterly

---

## 8. Relationship to Other v3.0 Controls

| Control | Relationship to CP.10 HEAR |
|---------|---------------------------|
| CP.9 (Agent Replication Governance) | HEAR holds the kill switch for the delegation tree governed by CP.9 |
| CP.8 (Catastrophic Risk Thresholds) | CRT triggers activate the Emergency Class-H protocol; HEAR exercises kill switch authority |
| P4.T7 (Human Oversight Controls) | HEAR extends P4.T7 from output review to action authorization with cryptographic accountability |
| A2.4 (Dynamic Agent State Inventory) | hear_agent_of_record field registers the HEAR for each ACT-3/ACT-4 deployment |
| A2.5 (Semantic Execution Trace Logging) | Records all Class-H authorizations, denials, and kill switch activations with HEAR signature |
| Section 12 (Sovereignty Scale) | HEAR is mandatory for S3 and S4 deployments; S4 requires full kill switch authority |
| F3.3 (Swarm Quorum Abort) | HEAR may trigger swarm abort unilaterally; quorum abort does not require HEAR approval but HEAR must be notified within 30 seconds of activation |

---

## References

- AI SAFE2 v3.0 Framework: CP.10 (HEAR Doctrine), CP.8, CP.9, Section 12 (Sovereignty Scale)
- AI SAFE2 Framework: research/012_the_engineered_liability_stack.md
- AI SAFE2 Framework: research/013_the_7_layer_stack.md
- AI SAFE2 Framework: AISM/agent-threat-control-matrix.md (T2: Multi-Agent Exploitation, T10: Insider and Operator Threats)
- CSI Threat Intelligence Dossier v4.0: HEAR Doctrine definition and RAND Corporation analysis (April 2026)
- EU AI Act (2024): Articles 9 and 14 (High-risk AI systems oversight requirements)
- SEC Cybersecurity Disclosure Rules (2023)
- SOC 2 Type II Trust Services Criteria: CC.7.4
- GDPR Article 22: Automated individual decision-making
