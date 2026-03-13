# AISM Self-Assessment Tool
## AI Sovereignty Matrix — Organizational Assessment Questionnaire

**Version:** 1.0  
**Date:** March 2026  
**Organization:** Cyber Strategy Institute  
**Framework:** AI SAFE2 v2.1 — AISM Scoring Methodology  
**Purpose:** Self-assessment for organizations to determine their AISM maturity level

---

## Instructions

### How to Use This Assessment

1. **Assemble your assessment team** — Include representatives from: Security/CISO office, AI/ML Engineering, Legal/Compliance, IT Operations, and Executive Leadership
2. **For each checklist item**, mark one of:
   - ✅ **Implemented** — Control is fully operational with evidence
   - 🔶 **Partial** — Control exists but is incomplete or inconsistent
   - ❌ **Not Implemented** — Control does not exist
   - ⬜ **N/A** — Not applicable to your organization
3. **Rate each section** using the three AISM metrics (Coverage, Robustness, Sovereignty Assurance) as Low/Medium/High
4. **Calculate your score** using the AISM Scoring Matrix (see Scoring Methodology document)
5. **Document evidence** for each implemented control

### Scoring Quick Reference

| Score | Metrics (Coverage / Robustness / Sovereignty) | Maturity Level |
|---|---|---|
| **5** | High / High / High | Autonomous Governance |
| **4** | High / High / Medium | Sovereign |
| **3** | Medium combinations (HMM, HHL, MMM, etc.) | Controlled |
| **2** | Low-medium combinations (MML, MLL, HLL) | Aware |
| **1** | Low / Low / Low | Reactive |

---

## Pillar 1: Sanitize / Isolate (P1)

### Topic 1: Sanitize — Input Validation, Data Filtering, Cleansing

#### Level 1 (Reactive) — Baseline Controls
- [ ] P1.T1.1 — Some form of input validation exists for AI systems
- [ ] P1.T1.4 — Basic content filtering is applied to AI outputs
- [ ] P1.T1.5 — PII is acknowledged as a concern in AI systems

#### Level 2 (Aware) — Foundation Controls
- [ ] P1.T1.1 — Input validation schemas are defined for primary AI systems
- [ ] P1.T1.2 — Basic prompt injection detection is in place
- [ ] P1.T1.3 — Data quality checks run on training data
- [ ] P1.T1.4 — Toxicity scoring mechanisms are deployed
- [ ] P1.T1.5 — PII/PHI masking is automated for primary systems
- [ ] P1.T1.6 — Input encoding validation (UTF-8) is enforced

#### Level 3 (Controlled) — Formalized Controls
- [ ] P1.T1.1 — All AI inputs validated against predefined schemas with rejection of malformed inputs
- [ ] P1.T1.2 — Adversarial prompt detection with semantic analysis across all endpoints
- [ ] P1.T1.3 — Statistical anomaly detection on all input data with automated profiling
- [ ] P1.T1.4 — Toxicity scoring with organizational policy enforcement
- [ ] P1.T1.5 — DLP controls with tokenization/pseudonymization of all sensitive fields
- [ ] P1.T1.6 — Homoglyph and invisible character injection prevention
- [ ] P1.T1.7 — SBOM generated and maintained; dependencies cross-referenced against CVE
- [ ] P1.T1.8 — Format normalization before tokenization across all pipelines
- [ ] P1.T1.9 — Cryptographic verification of imported models and datasets (SHA-256)

#### Level 4 (Sovereign) — Advanced Controls
- [ ] P1.T1.2-GF3 — OpenSSF Model Signing (OMS) verification at model load time
- [ ] P1.T1.2-GF3 — Provenance chain verification from base model through fine-tuning to deployment
- [ ] P1.T1.2-GF3 — Automated SBOM scanning with CVE correlation
- [ ] P1.T1.4-GF4 — Secret scanning in all AI outputs (credentials, API keys, tokens)
- [ ] P1.T1.4-GF4 — GitGuardian or equivalent integration for real-time secret detection
- [ ] P1.T1.4-GF4 — Pre-commit hooks for secret detection in AI codebases
- [ ] P1.T1.5-GF2/5 — SHA-256 hashing of agent state and context for integrity verification
- [ ] P1.T1.5-GF2/5 — Semantic similarity analysis for gradual poison injection detection
- [ ] P1.T1.5-GF2/5 — RAG poisoning detection with baseline embedding monitoring
- [ ] P1.T1.5-GF2/5 — Thread injection prevention with per-agent session isolation

#### Level 5 (Autonomous Governance) — Optimizing Controls
- [ ] All Level 4 controls with automated self-healing and continuous verification
- [ ] Formal verification of input validation logic
- [ ] Automated model fingerprinting triggers blocking on tampering detection
- [ ] AI-driven anomaly detection that adapts to new attack patterns without manual tuning
- [ ] Zero-trust input architecture — nothing trusted by default

**Section Rating:**
- Coverage: ☐ Low ☐ Medium ☐ High
- Robustness: ☐ Low ☐ Medium ☐ High
- Sovereignty Assurance: ☐ Low ☐ Medium ☐ High
- **Section Score: ___/5**

---

### Topic 2: Isolate — Containment, Sandboxing, Boundary Enforcement

#### Level 1 (Reactive)
- [ ] P1.T2.1 — AI systems run in shared environments with some access controls

#### Level 2 (Aware)
- [ ] P1.T2.1 — Agents deployed in basic isolated execution environments
- [ ] P1.T2.2 — AI workloads in dedicated network segments
- [ ] P1.T2.3 — API gateways with authentication deployed
- [ ] P1.T2.5 — Basic tool access restrictions for agents

#### Level 3 (Controlled)
- [ ] P1.T2.1 — Containerized agent deployment (Docker/Kubernetes) with resource limits
- [ ] P1.T2.2 — VLAN segmentation with firewall ACLs for AI systems
- [ ] P1.T2.3 — Rate limiting and IP/role-based API restrictions
- [ ] P1.T2.4 — Separate environments for model versions (dev/staging/prod)
- [ ] P1.T2.5 — Whitelist-based tool access with least privilege
- [ ] P1.T2.6 — Data encryption at rest and in transit; cross-tenant isolation
- [ ] P1.T2.7 — Hardened container images with vulnerability scanning
- [ ] P1.T2.8 — NGFW with IDS/IPS and egress filtering
- [ ] P1.T2.9 — Credentials stored in secret vaults with regular rotation

#### Level 4 (Sovereign)
- [ ] P1.T2.1-GF1 — Agent-to-agent communications isolated in dedicated network zones
- [ ] P1.T2.1-GF1 — A2A protocol restrictions with authentication/authorization/encryption
- [ ] P1.T2.1-GF1 — Automated agent quarantine on behavioral anomaly detection
- [ ] P1.T2.1-GF1 — P2P agent trust scoring with reputation weighting
- [ ] P1.T2.2-GF4 — Automated NHI discovery across cloud, on-premises, CI/CD
- [ ] P1.T2.2-GF4 — RBAC for all NHI entities
- [ ] P1.T2.2-GF4 — Just-in-time (JIT) privilege elevation
- [ ] P1.T2.2-GF4 — Automated decommissioning of inactive NHI (>90 days)

#### Level 5 (Autonomous Governance)
- [ ] All Level 4 controls with continuous automated verification
- [ ] Formal verification of boundary enforcement policies
- [ ] Self-adapting network segmentation based on threat intelligence
- [ ] Zero-trust agent architecture — every interaction authenticated and authorized

**Section Rating:**
- Coverage: ☐ Low ☐ Medium ☐ High
- Robustness: ☐ Low ☐ Medium ☐ High
- Sovereignty Assurance: ☐ Low ☐ Medium ☐ High
- **Section Score: ___/5**

---

## Pillar 2: Audit / Inventory (P2)

### Topic 3: Audit — Verification, Accountability, Tracking

#### Level 1 (Reactive)
- [ ] P2.T3.1 — Some logging exists for AI systems but not centralized

#### Level 2 (Aware)
- [ ] P2.T3.1 — Activity logging with timestamps for primary AI systems
- [ ] P2.T3.2 — Basic model performance monitoring (accuracy tracking)
- [ ] P2.T3.6 — Initial compliance mapping started

#### Level 3 (Controlled)
- [ ] P2.T3.1 — Tamper-proof, centralized logging with cryptographic signing
- [ ] P2.T3.2 — Automated data drift and concept drift detection with alerts
- [ ] P2.T3.3 — Behavioral baselines established with statistical anomaly detection
- [ ] P2.T3.4 — Explainability tracking (SHAP/LIME/attention maps) for all models
- [ ] P2.T3.5 — Bias/fairness metrics monitored across demographic groups
- [ ] P2.T3.6 — Controls mapped to SOC2, ISO 27001, NIST CSF with tracking
- [ ] P2.T3.7 — Decision provenance documented from input to output
- [ ] P2.T3.8 — All user interactions logged with prompt/query capture
- [ ] P2.T3.9 — Version control for all AI artifacts with change documentation
- [ ] P2.T3.10 — Regular vulnerability scans using MITRE ATLAS framework

#### Level 4 (Sovereign)
- [ ] P2.T1.1-GF4 — Dedicated NHI logging channels with real-time anomaly detection
- [ ] P2.T1.1-GF4 — Automated alerts on NHI credential misuse
- [ ] P2.T1.2-GF1/2 — Agent decision logs with full context and reasoning traces
- [ ] P2.T1.2-GF1/2 — Behavioral baseline profiling for each agent
- [ ] P2.T1.2-GF1/2 — Consensus voting audit trails for multi-agent systems
- [ ] P2.T1.2-GF1/2 — SHA-256 cryptographic hashing of agent state
- [ ] P2.T1.3-GF3 — Automated OMS signature verification in CI/CD
- [ ] P2.T1.3-GF3 — SBOM accuracy checks with dependency scanning
- [ ] P2.T1.4-GF5 — Periodic RAG content audits with semantic similarity checks
- [ ] P2.T1.4-GF5 — AgentPoison trigger phrase detection
- [ ] P2.T1.4-GF5 — Baseline embedding space monitoring

#### Level 5 (Autonomous Governance)
- [ ] All Level 4 controls with AI-driven continuous audit
- [ ] Formal verification of audit trail integrity
- [ ] Automated compliance reporting across all frameworks simultaneously
- [ ] Self-healing audit mechanisms that detect and correct gaps automatically

**Section Rating:**
- Coverage: ☐ Low ☐ Medium ☐ High
- Robustness: ☐ Low ☐ Medium ☐ High
- Sovereignty Assurance: ☐ Low ☐ Medium ☐ High
- **Section Score: ___/5**

---

### Topic 4: Inventory — Asset Mapping, Dependencies, Documentation

#### Level 1 (Reactive)
- [ ] P2.T4.1 — Some AI systems are informally known but no registry exists

#### Level 2 (Aware)
- [ ] P2.T4.1 — Basic AI system inventory maintained (spreadsheet or similar)
- [ ] P2.T4.2 — Model versions tracked informally
- [ ] P2.T4.8 — Some architecture documentation exists

#### Level 3 (Controlled)
- [ ] P2.T4.1 — Centralized AI system registry with owner, type, criticality, risk class
- [ ] P2.T4.2 — Model catalog with versions, release dates, training datasets, architectures
- [ ] P2.T4.3 — Agent capabilities, tools, autonomy levels, decision authority documented
- [ ] P2.T4.4 — All data sources mapped with lineage and refresh frequencies
- [ ] P2.T4.5 — API/MCP endpoint inventory with auth methods and rate limits
- [ ] P2.T4.6 — Tool/plugin registry with permissions and usage patterns
- [ ] P2.T4.7 — Dependency tracking with CVE cross-reference
- [ ] P2.T4.8 — Architecture diagrams and data flow documentation maintained
- [ ] P2.T4.9 — Centralized threat/risk register with mitigations
- [ ] P2.T4.10 — Configuration baselines with drift detection
- [ ] P2.T4.11 — SBOM generated for all models/applications

#### Level 4 (Sovereign)
- [ ] P2.T2.1-GF4 — Automated NHI discovery across all environments
- [ ] P2.T2.1-GF4 — Centralized NHI inventory with metadata (owner, purpose, permissions)
- [ ] P2.T2.1-GF4 — Lifecycle status tracking (active/inactive/decommissioned)
- [ ] P2.T2.1-GF4 — Automated alerts on stale NHI (>90 days inactive)
- [ ] P2.T2.2-GF1 — Agent registry with capabilities, tools, autonomy level per agent
- [ ] P2.T2.2-GF1 — Swarm topology diagrams and documentation
- [ ] P2.T2.2-GF1 — Orchestration platform version tracking (AutoGen, LangGraph, CrewAI)
- [ ] P2.T2.3-GF3 — Model artifact registry with SHA-256 hashes
- [ ] P2.T2.3-GF3 — SBOM version control and audit trails
- [ ] P2.T2.3-GF3 — Certificate expiration monitoring for model signing

#### Level 5 (Autonomous Governance)
- [ ] All Level 4 controls with automated continuous discovery and reconciliation
- [ ] Self-updating inventory via integration with CI/CD pipelines
- [ ] Dependency graph visualization with automated vulnerability alerting

**Section Rating:**
- Coverage: ☐ Low ☐ Medium ☐ High
- Robustness: ☐ Low ☐ Medium ☐ High
- Sovereignty Assurance: ☐ Low ☐ Medium ☐ High
- **Section Score: ___/5**

---

## Pillar 3: Fail-Safe / Recovery (P3)

### Topic 5: Fail-Safe — Shutdowns, Error Handling, Resilience

#### Level 1 (Reactive)
- [ ] P3.T5.2 — AI systems can be manually shut down if needed

#### Level 2 (Aware)
- [ ] P3.T5.1 — Basic circuit breakers in critical AI pipelines
- [ ] P3.T5.2 — Emergency shutdown documented for primary AI systems
- [ ] P3.T5.4 — Error handling prevents error propagation in most cases
- [ ] P3.T5.10 — Initial incident response procedures exist

#### Level 3 (Controlled)
- [ ] P3.T5.1 — Circuit breakers with graceful degradation paths tested regularly
- [ ] P3.T5.2 — Kill switches accessible to operators with escalation procedures
- [ ] P3.T5.3 — Failover to simpler models/rule-based systems defined and tested
- [ ] P3.T5.4 — Robust error handling with fail-closed/fail-open policies per risk level
- [ ] P3.T5.5 — Rate limiting on all API calls, model invocations, agent actions
- [ ] P3.T5.6 — Rollback procedures with version control, tested in staging
- [ ] P3.T5.7 — Redundant kill switches (hardware + software) with multi-stage shutdown
- [ ] P3.T5.8 — Blast radius containment via compartmentalization
- [ ] P3.T5.9 — Safe defaults enforced for all AI system configurations
- [ ] P3.T5.10 — Incident response playbooks for all identified AI threat scenarios

#### Level 4 (Sovereign)
- [ ] P3.T1.1-GF1 — Centralized kill switch for multi-agent systems
- [ ] P3.T1.1-GF1 — Automated agent isolation on anomalous behavior
- [ ] P3.T1.1-GF1 — Consensus failure escalation to human operators
- [ ] P3.T1.1-GF1 — Distributed quarantine with voting consensus
- [ ] P3.T1.2-GF4 — Automated NHI credential rotation
- [ ] P3.T1.2-GF4 — Service account disabling procedures with CRLs
- [ ] P3.T1.3-GF5 — Memory poisoning incident response playbook
- [ ] P3.T1.3-GF5 — RAG content quarantine and restoration procedures

#### Level 5 (Autonomous Governance)
- [ ] All Level 4 controls with automated self-recovery
- [ ] Formal verification of fail-safe logic
- [ ] AI-driven predictive failure detection and pre-emptive containment
- [ ] Self-healing systems that detect and remediate without human intervention

**Section Rating:**
- Coverage: ☐ Low ☐ Medium ☐ High
- Robustness: ☐ Low ☐ Medium ☐ High
- Sovereignty Assurance: ☐ Low ☐ Medium ☐ High
- **Section Score: ___/5**

---

### Topic 6: Recovery — Backups, Restoration, Continuity

#### Level 1 (Reactive)
- [ ] P3.T6.2 — Ad-hoc backup procedures exist for some AI data

#### Level 2 (Aware)
- [ ] P3.T6.1 — Model state backups exist for critical models
- [ ] P3.T6.4 — Basic disaster recovery plan includes AI systems
- [ ] P3.T6.6 — RTO/RPO targets defined for primary AI services

#### Level 3 (Controlled)
- [ ] P3.T6.1 — Automated model state backups with version tracking
- [ ] P3.T6.2 — Data recovery procedures documented and tested
- [ ] P3.T6.3 — Automated backup scheduling for all AI artifacts
- [ ] P3.T6.4 — Comprehensive disaster recovery plan tested annually
- [ ] P3.T6.5 — Business continuity procedures cover AI service disruptions
- [ ] P3.T6.6 — RTO/RPO tracked and validated for all AI systems
- [ ] P3.T6.7 — Recovery procedures tested and validated regularly
- [ ] P3.T6.8 — Off-site backup storage for critical AI models and data
- [ ] P3.T6.9 — Configuration restoration procedures documented
- [ ] P3.T6.10 — Post-incident forensics with documented post-mortems

#### Level 4 (Sovereign)
- [ ] P3.T2.1-GF1 — Agent state and memory backups with version control
- [ ] P3.T2.1-GF1 — Multi-agent system state snapshots
- [ ] P3.T2.2-GF4 — NHI credential backup/escrow with automated rotation
- [ ] P3.T2.2-GF4 — HSM integration for credential key management
- [ ] P3.T2.2-GF4 — Fallback authentication methods for NHI

#### Level 5 (Autonomous Governance)
- [ ] All Level 4 controls with zero-touch automated recovery
- [ ] Sub-minute RTO for critical AI services
- [ ] Self-validating recovery that confirms system integrity post-restoration

**Section Rating:**
- Coverage: ☐ Low ☐ Medium ☐ High
- Robustness: ☐ Low ☐ Medium ☐ High
- Sovereignty Assurance: ☐ Low ☐ Medium ☐ High
- **Section Score: ___/5**

---

## Pillar 4: Engage / Monitor (P4)

### Topic 7: Engage — Human Oversight, Intervention, Interaction

#### Level 1 (Reactive)
- [ ] P4.T7.5 — Someone can intervene if an AI system behaves unexpectedly

#### Level 2 (Aware)
- [ ] P4.T7.1 — Human approval required for some high-risk AI actions
- [ ] P4.T7.4 — Escalation procedures exist but are informal
- [ ] P4.T7.6 — User interactions with AI systems are observed sporadically

#### Level 3 (Controlled)
- [ ] P4.T7.1 — Human approval workflows for all critical AI actions
- [ ] P4.T7.2 — Explainability/reasoning transparency for key decisions
- [ ] P4.T7.3 — Feedback loops for fine-tuning based on user input
- [ ] P4.T7.4 — Tiered escalation procedures with alert routing
- [ ] P4.T7.5 — Real-time human intervention capability for all production AI
- [ ] P4.T7.6 — All user interactions monitored and logged
- [ ] P4.T7.7 — Regular red team/adversarial testing of AI systems
- [ ] P4.T7.8 — Risk acceptance with documented exception handling
- [ ] P4.T7.9 — Cross-functional AI governance collaboration established
- [ ] P4.T7.10 — Stakeholder transparency reporting implemented

#### Level 4 (Sovereign)
- [ ] P4.T1.1-GF1 — Human approval gates for multi-agent consensus decisions
- [ ] P4.T1.1-GF1 — Consensus failure automatically escalates to human operators
- [ ] P4.T1.1-GF1 — Human override capability for all agent swarm actions
- [ ] P4.T1.2-GF4 — NHI privilege elevation requires human review
- [ ] P4.T1.2-GF4 — Just-in-time access with anomalous access alerts
- [ ] P4.T1.2-GF4 — Baseline validation for all NHI privilege changes

#### Level 5 (Autonomous Governance)
- [ ] All Level 4 controls with adaptive human oversight
- [ ] AI-assisted oversight that surfaces only highest-priority decisions to humans
- [ ] Continuous stakeholder transparency with real-time dashboards
- [ ] Formal verification of human-in-the-loop mechanisms

**Section Rating:**
- Coverage: ☐ Low ☐ Medium ☐ High
- Robustness: ☐ Low ☐ Medium ☐ High
- Sovereignty Assurance: ☐ Low ☐ Medium ☐ High
- **Section Score: ___/5**

---

### Topic 8: Monitor — Observation, Anomaly Detection, Logging

#### Level 1 (Reactive)
- [ ] P4.T8.3 — Basic security logs exist for AI infrastructure

#### Level 2 (Aware)
- [ ] P4.T8.1 — Basic performance dashboards for primary AI systems
- [ ] P4.T8.3 — SIEM integration for AI security events
- [ ] P4.T8.5 — Token usage tracked for cost management

#### Level 3 (Controlled)
- [ ] P4.T8.1 — Real-time performance dashboards for all production AI systems
- [ ] P4.T8.2 — Anomaly detection with automated alerting
- [ ] P4.T8.3 — Full SIEM integration with AI-specific event correlation
- [ ] P4.T8.4 — Model accuracy and drift monitoring with alerts
- [ ] P4.T8.5 — Token usage and cost tracking across all AI systems
- [ ] P4.T8.6 — Latency and performance metrics collected and baselined
- [ ] P4.T8.7 — Error rates tracked with failure pattern analysis
- [ ] P4.T8.8 — API usage quotas monitored with anomaly alerts
- [ ] P4.T8.9 — Data quality metrics tracked for all AI data sources
- [ ] P4.T8.10 — Compliance audit logs generated automatically

#### Level 4 (Sovereign)
- [ ] P4.T2.1-GF1 — Distributed agent health monitoring with consensus validation
- [ ] P4.T2.1-GF1 — Multi-node anomaly detection with voting consensus
- [ ] P4.T2.1-GF1 — Agent communication pattern monitoring
- [ ] P4.T2.2-GF4 — Real-time NHI activity dashboard
- [ ] P4.T2.2-GF4 — Behavioral anomaly detection for all NHI entities
- [ ] P4.T2.2-GF4 — Unusual API call alerting for service accounts
- [ ] P4.T2.3-GF5 — Context consistency verification for agent sessions
- [ ] P4.T2.3-GF5 — Embedding space monitoring for semantic drift
- [ ] P4.T2.3-GF5 — RAG integrity monitoring with baseline comparison

#### Level 5 (Autonomous Governance)
- [ ] All Level 4 controls with self-tuning monitoring thresholds
- [ ] Predictive monitoring that anticipates issues before they manifest
- [ ] Automated response to monitoring alerts (containment, escalation, recovery)

**Section Rating:**
- Coverage: ☐ Low ☐ Medium ☐ High
- Robustness: ☐ Low ☐ Medium ☐ High
- Sovereignty Assurance: ☐ Low ☐ Medium ☐ High
- **Section Score: ___/5**

---

## Pillar 5: Evolve / Educate (P5)

### Topic 9: Evolve — Threat Adaptation, Continuous Improvement

#### Level 1 (Reactive)
- [ ] P5.T9.4 — Security patches applied when notified by vendors

#### Level 2 (Aware)
- [ ] P5.T9.1 — Threat intelligence feeds monitored for AI-relevant threats
- [ ] P5.T9.4 — Patch management process includes AI infrastructure
- [ ] P5.T9.10 — Some lessons learned captured after incidents

#### Level 3 (Controlled)
- [ ] P5.T9.1 — Threat intelligence integrated into AI risk assessments
- [ ] P5.T9.2 — Playbooks and controls updated based on new threats
- [ ] P5.T9.3 — Model retraining scheduled with performance triggers
- [ ] P5.T9.4 — Security patches applied within defined SLAs
- [ ] P5.T9.5 — Dependencies updated with CVE correlation
- [ ] P5.T9.6 — Policies and procedures reviewed and updated periodically
- [ ] P5.T9.7 — Emerging threat response procedures defined
- [ ] P5.T9.8 — Capability enhancements planned and tracked
- [ ] P5.T9.9 — Performance optimization processes established
- [ ] P5.T9.10 — Formal incident lessons learned with action tracking

#### Level 4 (Sovereign)
- [ ] P5.T1.1-GF1 — Agent swarm capability evolution tracked and managed
- [ ] P5.T1.1-GF1 — Multi-agent system security enhancements planned
- [ ] P5.T1.2-GF3 — OMS specification updates tracked and adopted
- [ ] P5.T1.2-GF3 — SBOM format evolution incorporated
- [ ] P5.T1.3-GF4 — NHI lifecycle process improvements tracked
- [ ] P5.T1.3-GF4 — Secret rotation policy tuning based on threat intel
- [ ] P5.T1.4-GF5 — Memory poisoning defense techniques updated with latest research
- [ ] P5.T1.4-GF5 — AgentPoison/MINJA/PajaMAS mitigations current

#### Level 5 (Autonomous Governance)
- [ ] All Level 4 controls with automated threat adaptation
- [ ] AI-driven continuous improvement recommendations
- [ ] Self-evolving controls that adapt to new threat patterns autonomously
- [ ] Research integration pipeline that incorporates academic findings within 30 days

**Section Rating:**
- Coverage: ☐ Low ☐ Medium ☐ High
- Robustness: ☐ Low ☐ Medium ☐ High
- Sovereignty Assurance: ☐ Low ☐ Medium ☐ High
- **Section Score: ___/5**

---

### Topic 10: Educate — Training, Culture, Awareness

#### Level 1 (Reactive)
- [ ] P5.T10.2 — General cybersecurity awareness mentions AI risks

#### Level 2 (Aware)
- [ ] P5.T10.1 — Basic operator training for primary AI systems
- [ ] P5.T10.2 — AI security awareness included in annual training
- [ ] P5.T10.3 — Basic safe prompt engineering guidelines shared

#### Level 3 (Controlled)
- [ ] P5.T10.1 — Comprehensive operator training for all AI system types
- [ ] P5.T10.2 — Dedicated AI security awareness training program
- [ ] P5.T10.3 — Safe prompt engineering education with hands-on exercises
- [ ] P5.T10.4 — Regular incident response drills for AI-specific scenarios
- [ ] P5.T10.5 — Policies and procedures communicated to all stakeholders
- [ ] P5.T10.6 — Industry best practices shared with teams
- [ ] P5.T10.7 — Internal AI documentation/wiki maintained
- [ ] P5.T10.8 — Vendor security training requirements established
- [ ] P5.T10.9 — Role-based training (developers, operators, leaders)
- [ ] P5.T10.10 — Culture of AI accountability established with framework

#### Level 4 (Sovereign)
- [ ] P5.T2.1-GF1 — Agent operator and swarm manager training programs
- [ ] P5.T2.1-GF1 — Multi-agent system security training with hands-on labs
- [ ] P5.T2.1-GF1 — Emerging threat briefings for agentic AI
- [ ] P5.T2.2-GF4 — NHI threat awareness training for all developers
- [ ] P5.T2.2-GF4 — Secret hygiene education with incident response procedures
- [ ] P5.T2.3-GF3 — Supply chain and model security culture training
- [ ] P5.T2.3-GF3 — SBOM literacy for development teams
- [ ] P5.T2.4-GF5 — RAG security training for all developers building RAG systems
- [ ] P5.T2.4-GF5 — AgentPoison awareness modules with real-world examples
- [ ] P5.T2.4-GF5 — Prompt injection prevention training with hands-on exercises

#### Level 5 (Autonomous Governance)
- [ ] All Level 4 controls with continuous learning culture
- [ ] AI-specific certification paths for all AI practitioners
- [ ] Organization-wide AI safety culture with measurable outcomes
- [ ] Continuous education that adapts to new research and threats

**Section Rating:**
- Coverage: ☐ Low ☐ Medium ☐ High
- Robustness: ☐ Low ☐ Medium ☐ High
- Sovereignty Assurance: ☐ Low ☐ Medium ☐ High
- **Section Score: ___/5**

---

## Overall AISM Score Summary

| Pillar | Topic | Score (1–5) |
|---|---|---|
| **P1: Sanitize / Isolate** | T1: Sanitize | ___/5 |
| | T2: Isolate | ___/5 |
| | **Pillar P1 Average** | **___/5** |
| **P2: Audit / Inventory** | T3: Audit | ___/5 |
| | T4: Inventory | ___/5 |
| | **Pillar P2 Average** | **___/5** |
| **P3: Fail-Safe / Recovery** | T5: Fail-Safe | ___/5 |
| | T6: Recovery | ___/5 |
| | **Pillar P3 Average** | **___/5** |
| **P4: Engage / Monitor** | T7: Engage | ___/5 |
| | T8: Monitor | ___/5 |
| | **Pillar P4 Average** | **___/5** |
| **P5: Evolve / Educate** | T9: Evolve | ___/5 |
| | T10: Educate | ___/5 |
| | **Pillar P5 Average** | **___/5** |
| | | |
| **Overall AISM Sovereignty Score** | | **___/5** |

### Maturity Classification

| Score | Level | Classification |
|---|---|---|
| 4.50 – 5.00 | 5 | **Autonomous Governance** — AI sovereignty fully realized |
| 3.50 – 4.49 | 4 | **Sovereign** — Full visibility and adaptive control |
| 2.50 – 3.49 | 3 | **Controlled** — Formalized controls, documented processes |
| 1.50 – 2.49 | 2 | **Aware** — Basic policies, inconsistent application |
| 1.00 – 1.49 | 1 | **Reactive** — Ad-hoc, incident-driven |

---

## Assessment Completion

| Item | Details |
|---|---|
| **Organization Name** | |
| **Assessment Date** | |
| **Assessment Team Lead** | |
| **Team Members** | |
| **Overall AISM Score** | |
| **Maturity Classification** | |
| **Priority Gaps Identified** | |
| **Next Review Date** | |

---

## References

1. Cyber Strategy Institute (2025). AI SAFE2 Framework v2.1.
2. Dotan et al. (2024). IEEE/NIST AI RMF Flexible Maturity Model.
3. Microsoft Research (2023). Responsible AI Maturity Model.
4. Cloud Security Alliance (2025). AI Controls Matrix (AICM) v1.0.
5. Bernardo et al. (2025). NIST CSF Maturity Assessment Framework.
6. Darling et al. (2026). Maturity-Based Certification for Embodied AI.

---

*© 2026 Cyber Strategy Institute. Licensed under CC BY 4.0.*
