
<div align="center">
  <img src="../assets/AISM Compliance Crosswalk v2.png" alt="AISM Compliance Crosswalk" width="100%" />
</div>

# AISM Compliance Crosswalk
## AI SAFE2 Framework v3.0 — Cross-Framework Compliance Mapping

**Version:** 1.0  
**Date:** March 2026  
**Organization:** Cyber Strategy Institute  
**Purpose:** Enterprise procurement, audit readiness, and multi-framework compliance reporting

---

## 1. Overview

This crosswalk maps every AI SAFE2 v3.0 pillar, topic, and maturity level to:
- **NIST AI RMF 1.0** (Govern, Map, Measure, Manage)
- **ISO/IEC 42001:2022** (AI Management System clauses)
- **EU AI Act** (Articles for high-risk AI systems)
- **CSA AICM** (AI Controls Matrix domains/control IDs)
- **NIST CSF 2.0** (Functions: Govern, Identify, Protect, Detect, Respond, Recover)
- **MITRE ATLAS** (Adversarial threat techniques)
- **OWASP Top 10 for LLM** (LLM01–LLM10)

---

## 2. Pillar 1: Sanitize / Isolate (P1)

### Topic 1: Sanitize (P1.T1) — Input Validation, Data Filtering, Cleansing

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P1.T1.1 Input Validation Schema Enforcement | MEASURE 2.9 | 8.2.2 | Art. 10(2) | DSP (Data Security & Privacy) | PR.DS | — | — |
| P1.T1.2 Malicious Prompt Filtering / Injection Prevention | MANAGE 2.2, MEASURE 2.9 | 8.2.2, 8.4 | Art. 15(4) | AIS (AI Security) | PR.DS, DE.CM | AML.T0051 | LLM01, LLM02 |
| P1.T1.3 Data Quality Checks / Anomaly Detection | MAP 2.3, MEASURE 2.6 | 8.2.2 | Art. 10(2-3) | DLM (Data Lifecycle Mgmt) | ID.RA | — | LLM03 |
| P1.T1.4 Toxic Content Detection / Filtering | MEASURE 2.11 | 8.2.2 | Art. 5(1) | AIS | PR.DS | — | LLM02 |
| P1.T1.5 Sensitive Data Masking / Redaction (PII/PHI) | MANAGE 3.1, GOVERN 1.4 | 8.2.2, 8.3.3 | Art. 10(5) | DSP | PR.DS | AML.T0057 | LLM06 |
| P1.T1.6 Format Normalization / Encoding Validation | MEASURE 2.9 | 8.2.2 | Art. 15(4) | DSP | PR.DS | — | — |
| P1.T1.7 Dependency Verification / SBOM Checks | MAP 5.2, GOVERN 6.2 | 8.2.4 | Art. 15(2) | STA (Supply Chain & Transparency) | ID.AM | — | LLM05, LLM10 |
| P1.T1.8 Format Normalization / Encoding Validation (Extended) | MEASURE 2.9 | 8.2.2 | Art. 15(4) | DSP | PR.DS | — | — |
| P1.T1.9 Supply Chain Artifact Validation | MAP 5.2, GOVERN 6.2 | 8.2.4 | Art. 15(2) | STA | ID.SC | AML.T0010 | LLM05, LLM10 |

#### Gap Filler Subtopics (v3.0)

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P1.T1.2 Supply Chain Artifact Validation (GF3) | GOVERN 6.2, MAP 5.2 | 8.2.4 | Art. 15(2) | STA | ID.SC | AML.T0002, AML.T0005 | LLM05 |
| P1.T1.4 NHI Secret Validation / Hygiene (GF4) | MANAGE 2.2 | 8.3.3 | Art. 15(3) | IAM (Identity & Access Mgmt) | PR.AC | — | LLM06 |
| P1.T1.5 Memory-Specific Attack Mitigation (GF2/5) | MEASURE 2.9, MANAGE 2.2 | 8.4 | Art. 15(4) | AIS | DE.CM | AML.T0000.001, AML.T0001 | LLM03 |

### Topic 2: Isolate (P1.T2) — Containment, Sandboxing, Boundary Enforcement

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P1.T2.1 Agent Sandboxing / Resource Containment | MANAGE 2.2, MAP 1.6 | 8.3.3 | Art. 15(3) | IVS (Infrastructure & Virtualization Security) | PR.AC | — | LLM08 |
| P1.T2.2 Network Segmentation for AI Systems | MANAGE 2.2 | 8.3.3 | Art. 15(3) | IVS | PR.AC | — | — |
| P1.T2.3 API Gateway Restrictions / Rate Limiting | MANAGE 2.2 | 8.3.3 | Art. 15(3) | AIS | PR.AC | AML.T0040 | LLM08 |
| P1.T2.4 Model Versioning / Isolation | GOVERN 1.6 | 8.1 | Art. 12(2) | GRC (Governance, Risk & Compliance) | PR.DS | — | — |
| P1.T2.5 Tool/Function Access Control / Whitelisting | MANAGE 2.2 | 8.3.3 | Art. 14(4) | IAM | PR.AC | — | LLM08 |
| P1.T2.6 Data Isolation / Access Boundaries | MANAGE 3.1 | 8.2.2, 8.3.3 | Art. 10(5) | DSP | PR.DS | — | LLM06 |
| P1.T2.7 Container Security / Runtime Isolation | MANAGE 2.2 | 8.3.3 | Art. 15(3) | IVS | PR.IP | — | — |
| P1.T2.8 Firewall / Network Perimeter Controls | MANAGE 2.2 | 8.3.3 | Art. 15(3) | IVS | PR.AC | — | — |
| P1.T2.9 API Key / Credential Compartmentalization | MANAGE 2.2 | 8.3.3 | Art. 15(3) | IAM | PR.AC | — | — |

#### Gap Filler Subtopics (v3.0)

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P1.T2.1 Multi-Agent Boundary Enforcement (GF1) | MANAGE 2.2 | 8.3.3 | Art. 15(3) | IVS, AIS | PR.AC | Agent-specific tactics (Oct 2025) | LLM08 |
| P1.T2.2 NHI Access Control / Least Privilege (GF4) | MANAGE 2.2 | 8.3.3 | Art. 15(3) | IAM | PR.AC | — | — |

---

## 3. Pillar 2: Audit / Inventory (P2)

### Topic 3: Audit (P2.T3) — Verification, Accountability, Tracking

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P2.T3.1 Real-Time Activity Logging / Audit Trails | GOVERN 1.4, MEASURE 2.6 | 8.4 | Art. 12(1) | LOG (Logging & Monitoring) | DE.AE | — | — |
| P2.T3.2 Model Performance Monitoring / Drift Detection | MEASURE 2.6, MEASURE 2.11 | 8.4 | Art. 9(8) | AIS | DE.CM | — | — |
| P2.T3.3 Behavior Verification / Anomaly Detection | MEASURE 2.6, MEASURE 2.9 | 8.4 | Art. 9(8) | AIS | DE.AE | — | — |
| P2.T3.4 Explainability / Interpretability Tracking | GOVERN 1.4, MAP 2.2 | 8.4 | Art. 13(1) | TRN (Transparency) | ID.GV | — | LLM09 |
| P2.T3.5 Bias / Fairness Monitoring | MEASURE 2.11 | 8.4 | Art. 10(2-f) | AIS | ID.RA | — | — |
| P2.T3.6 Compliance Framework Validation | GOVERN 1.1, GOVERN 3.2 | 8.1, 9.2 | Art. 17(1) | GRC | GV.OC | — | — |
| P2.T3.7 Decision Traceability / Provenance | GOVERN 1.4, MAP 2.2 | 8.4 | Art. 12(1) | TRN | DE.AE | — | — |
| P2.T3.8 User Interaction Logging | MEASURE 2.6 | 8.4 | Art. 12(1) | LOG | DE.AE | — | — |
| P2.T3.9 AI System Change Tracking | GOVERN 1.6, MANAGE 4.1 | 8.1 | Art. 12(2) | GRC | PR.IP | — | — |
| P2.T3.10 Vulnerability Scanning / Threat Assessment | MEASURE 2.9 | 8.4 | Art. 9(5) | TVM (Threat & Vulnerability Mgmt) | ID.RA | Full ATLAS mapping | — |

#### Gap Filler Subtopics (v3.0)

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P2.T1.1 NHI Activity Logging / Audit Trail (GF4) | GOVERN 1.4 | 8.4 | Art. 12(1) | LOG, IAM | DE.AE | — | — |
| P2.T1.2 Agent Behavior / State Verification (GF1/2) | MEASURE 2.6 | 8.4 | Art. 9(8) | AIS | DE.AE | Agent-specific tactics | — |
| P2.T1.3 Supply Chain Artifact Audit / Provenance (GF3) | GOVERN 6.2 | 8.2.4 | Art. 15(2) | STA | ID.SC | AML.T0002 | LLM05 |
| P2.T1.4 Memory Poisoning / Context Injection Detection (GF5) | MEASURE 2.9 | 8.4 | Art. 15(4) | AIS | DE.CM | AML.T0000.001 | LLM03 |

### Topic 4: Inventory (P2.T4) — Asset Mapping, Dependencies

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P2.T4.1 AI System Inventory / Registry | MAP 1.1, GOVERN 1.6 | 8.1 | Art. 60(1) | GRC | ID.AM | — | — |
| P2.T4.2 Model Catalog / Versioning | GOVERN 1.6 | 8.1 | Art. 12(2) | GRC | ID.AM | — | — |
| P2.T4.3 Agent Capability Documentation | MAP 1.1, MAP 3.1 | 8.1 | Art. 11(1) | TRN | ID.AM | — | — |
| P2.T4.4 Data Source Mapping | MAP 2.3 | 8.2.2 | Art. 10(2) | DLM | ID.AM | — | — |
| P2.T4.5 API / MCP Endpoint Inventory | MAP 5.2 | 8.1 | Art. 15(2) | AIS | ID.AM | — | — |
| P2.T4.6 Tool / Plugin Registry | MAP 5.2 | 8.1 | Art. 15(2) | AIS | ID.AM | — | LLM07 |
| P2.T4.7 Dependency Tracking | MAP 5.2, GOVERN 6.2 | 8.2.4 | Art. 15(2) | STA | ID.AM | — | LLM05 |
| P2.T4.8 Architecture Documentation | MAP 1.1 | 8.1 | Art. 11(1) | TRN | ID.AM | — | — |
| P2.T4.9 Threat / Risk Registers | MAP 5.1, MAP 5.2 | 8.1 | Art. 9(2) | TVM | ID.RA | Full ATLAS mapping | — |
| P2.T4.10 Configuration Baseline Tracking | MANAGE 4.1 | 8.1 | Art. 12(2) | GRC | PR.IP | — | — |
| P2.T4.11 SBOM Generation / Tracking | GOVERN 6.2 | 8.2.4 | Art. 15(2) | STA | ID.AM | — | LLM05, LLM10 |

#### Gap Filler Subtopics (v3.0

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P2.T2.1 NHI Registry / Lifecycle Management (GF4) | GOVERN 1.6 | 8.1, 8.3.3 | Art. 15(3) | IAM | ID.AM | — | — |
| P2.T2.2 Agent Architecture / Agentic System Inventory (GF1) | MAP 1.1 | 8.1 | Art. 11(1) | TRN | ID.AM | Agent subdomain (Apr 2025) | — |
| P2.T2.3 Supply Chain / Model Artifact Inventory (GF3) | GOVERN 6.2 | 8.2.4 | Art. 15(2) | STA | ID.SC | AML.T0002 | LLM05 |

---

## 4. Pillar 3: Fail-Safe / Recovery (P3)

### Topic 5: Fail-Safe (P3.T5)

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P3.T5.1 Circuit Breaker Patterns / Graceful Degradation | MANAGE 2.4 | 8.4 | Art. 15(5) | BCR (Business Continuity & Resilience) | RC.RP | — | — |
| P3.T5.2 Emergency Shutdown Procedures | MANAGE 2.4 | 8.4 | Art. 14(4-e) | BCR | RS.RP | — | LLM08 |
| P3.T5.3 Fallback Mechanisms / Failover Strategies | MANAGE 2.4 | 8.4 | Art. 15(5) | BCR | RC.RP | — | — |
| P3.T5.4 Error Handling / Exception Management | MANAGE 2.4 | 8.4 | Art. 15(5) | BCR | RS.AN | — | — |
| P3.T5.5 Rate Limiting / Resource Throttling | MANAGE 2.2 | 8.3.3 | Art. 15(4) | AIS | PR.DS | — | LLM04 |
| P3.T5.6 Rollback Procedures / Version Control | MANAGE 4.1 | 8.1 | Art. 12(2) | GRC | RC.RP | — | — |
| P3.T5.7 Kill Switches for Runaway Agents | MANAGE 2.4 | 8.4 | Art. 14(4-e) | BCR | RS.RP | — | LLM08 |
| P3.T5.8 Blast Radius Containment | MANAGE 2.2 | 8.3.3 | Art. 15(3) | BCR | PR.AC | — | — |
| P3.T5.9 Safe Defaults / Defensive Programming | MANAGE 2.2 | 8.4 | Art. 15(4) | AIS | PR.DS | — | — |
| P3.T5.10 Incident Response Playbooks | MANAGE 4.3 | 8.4 | Art. 62(1) | SEF (Security Incident Mgmt) | RS.RP | — | — |

#### Gap Filler Subtopics (v3.0)

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P3.T1.1 Distributed Agent Fail-Safe / Quarantine (GF1) | MANAGE 2.4 | 8.4 | Art. 14(4-e) | BCR, AIS | RS.RP | Agent-specific tactics | LLM08 |
| P3.T1.2 NHI Credential Revocation / Emergency Disable (GF4) | MANAGE 2.2 | 8.3.3 | Art. 15(3) | IAM | RS.RP | — | — |
| P3.T1.3 Memory Poisoning Incident Response (GF5) | MANAGE 4.3 | 8.4 | Art. 62(1) | SEF | RS.RP | AML.T0000.001 | LLM03 |

### Topic 6: Recovery (P3.T6)

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P3.T6.1 Model State Backups | MANAGE 4.1 | 8.1 | Art. 12(2) | BCR | RC.RP | — | — |
| P3.T6.2 Data Recovery Procedures | MANAGE 4.1 | 8.1 | Art. 15(5) | BCR | RC.RP | — | — |
| P3.T6.3 Backup Automation / Scheduling | MANAGE 4.1 | 8.1 | Art. 15(5) | BCR | RC.RP | — | — |
| P3.T6.4 Disaster Recovery Planning | MANAGE 4.1 | 8.1 | Art. 15(5) | BCR | RC.RP | — | — |
| P3.T6.5 Business Continuity Procedures | MANAGE 4.1 | 8.1 | Art. 15(5) | BCR | RC.RP | — | — |
| P3.T6.6 RTO/RPO Management | MANAGE 4.1 | 8.1 | Art. 15(5) | BCR | RC.RP | — | — |
| P3.T6.7 Testing / Validation of Recovery | MANAGE 4.1 | 8.4 | Art. 15(5) | BCR | RC.RP | — | — |
| P3.T6.8 Off-Site Backup Storage | MANAGE 4.1 | 8.1 | Art. 15(5) | BCR | RC.RP | — | — |
| P3.T6.9 Configuration Restoration | MANAGE 4.1 | 8.1 | Art. 12(2) | GRC | RC.RP | — | — |
| P3.T6.10 Incident Forensics / Post-Mortems | MANAGE 4.3 | 8.4 | Art. 62(1) | SEF | RS.AN | — | — |

#### Gap Filler Subtopics (v3.0)

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P3.T2.1 Agent State / Memory Backups (GF1) | MANAGE 4.1 | 8.1 | Art. 12(2) | BCR | RC.RP | — | — |
| P3.T2.2 NHI Credential Recovery / Rotation (GF4) | MANAGE 2.2 | 8.3.3 | Art. 15(3) | IAM | RC.RP | — | — |

---

## 5. Pillar 4: Engage / Monitor (P4)

### Topic 7: Engage (P4.T7)

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P4.T7.1 Human Approval Workflows | GOVERN 5.1, MAP 3.4 | 8.4 | Art. 14(1-3) | GRC | GV.RR | — | LLM09 |
| P4.T7.2 Explainability / Reasoning Transparency | GOVERN 1.4, MAP 2.2 | 8.4 | Art. 13(1) | TRN | GV.OC | — | LLM09 |
| P4.T7.3 Interactive Feedback / Fine-Tuning Loops | MANAGE 4.1, MEASURE 2.6 | 8.5 | Art. 14(4-b) | AIS | DE.CM | — | — |
| P4.T7.4 Escalation Procedures / Alert Routing | MANAGE 4.3 | 8.4 | Art. 14(4-d) | SEF | RS.CO | — | — |
| P4.T7.5 Real-Time Human Intervention | GOVERN 5.1 | 8.4 | Art. 14(4-e) | GRC | RS.RP | — | — |
| P4.T7.6 User Interaction Oversight | MEASURE 2.6 | 8.4 | Art. 14(4-a) | LOG | DE.CM | — | — |
| P4.T7.7 Red Team / Adversarial Testing | MEASURE 2.9, MANAGE 2.2 | 8.4 | Art. 9(6) | AIS | DE.DP | Full ATLAS mapping | — |
| P4.T7.8 Risk Acceptance / Exception Handling | GOVERN 1.3 | 6.1 | Art. 9(4) | GRC | GV.RM | — | — |
| P4.T7.9 Cross-Functional Collaboration | GOVERN 2.2 | 5.3 | Art. 17(1-k) | GRC | GV.RR | — | — |
| P4.T7.10 Stakeholder Transparency / Reporting | GOVERN 1.4, GOVERN 5.2 | 9.3 | Art. 13(1) | TRN | GV.OC | — | — |

#### Gap Filler Subtopics (v3.0)

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P4.T1.1 Human Approval for Multi-Agent Decisions (GF1) | GOVERN 5.1 | 8.4 | Art. 14(1-3) | GRC | GV.RR | Agent-specific tactics | LLM08 |
| P4.T1.2 NHI Privilege Elevation Review (GF4) | MANAGE 2.2 | 8.3.3 | Art. 15(3) | IAM | PR.AC | — | — |

### Topic 8: Monitor (P4.T8)

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P4.T8.1 Real-Time Performance Dashboards | MEASURE 2.6 | 8.4 | Art. 9(8) | LOG | DE.CM | — | — |
| P4.T8.2 Anomaly Detection / Alerting | MEASURE 2.9, MEASURE 2.6 | 8.4 | Art. 9(8) | AIS | DE.AE | — | — |
| P4.T8.3 Security Event Logging / SIEM Integration | MEASURE 2.9 | 8.4 | Art. 12(1) | LOG | DE.AE | — | — |
| P4.T8.4 Model Accuracy / Drift Monitoring | MEASURE 2.6, MEASURE 2.11 | 8.4 | Art. 9(8) | AIS | DE.CM | — | — |
| P4.T8.5 Token Usage / Cost Tracking | GOVERN 1.3 | 8.1 | — | GRC | GV.RM | — | — |
| P4.T8.6 Latency / Performance Metrics | MEASURE 2.6 | 8.4 | Art. 15(1) | AIS | DE.CM | — | — |
| P4.T8.7 Error Rate / Failure Tracking | MEASURE 2.6 | 8.4 | Art. 9(8) | LOG | DE.CM | — | — |
| P4.T8.8 API Usage / Quota Monitoring | MANAGE 2.2 | 8.3.3 | Art. 15(4) | AIS | DE.CM | — | — |
| P4.T8.9 Data Quality Metrics | MEASURE 2.6 | 8.2.2 | Art. 10(2) | DLM | DE.CM | — | — |
| P4.T8.10 Compliance Audit Logs | GOVERN 1.1, GOVERN 3.2 | 9.2 | Art. 17(1) | GRC | GV.OC | — | — |

#### Gap Filler Subtopics (v3.0)

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P4.T2.1 Distributed Agent Health / Consensus Monitoring (GF1) | MEASURE 2.6 | 8.4 | Art. 9(8) | AIS | DE.CM | Agent-specific tactics | — |
| P4.T2.2 NHI Activity Monitoring / Anomaly Detection (GF4) | MEASURE 2.9 | 8.4 | Art. 12(1) | IAM, LOG | DE.AE | — | — |
| P4.T2.3 Memory Poisoning / Context Injection Monitoring (GF5) | MEASURE 2.9 | 8.4 | Art. 15(4) | AIS | DE.CM | AML.T0000.001 | LLM03 |

---

## 6. Pillar 5: Evolve / Educate (P5)

### Topic 9: Evolve (P5.T9)

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P5.T9.1 Threat Intelligence Integration / Updates | MANAGE 4.1, MEASURE 2.9 | 8.5 | Art. 9(9) | TVM | ID.RA | Full ATLAS mapping | — |
| P5.T9.2 Playbook / Control Updates | MANAGE 4.1, GOVERN 1.3 | 8.5, 10.1 | Art. 9(9) | SEF | RS.IM | — | — |
| P5.T9.3 Model Retraining / Refinement | MANAGE 4.1, MEASURE 2.6 | 8.5 | Art. 15(4) | AIS | PR.IP | — | — |
| P5.T9.4 Security Patch Management | MANAGE 4.1 | 8.5 | Art. 15(2) | TVM | PR.IP | — | — |
| P5.T9.5 Dependency Updates / Remediation | MANAGE 4.1, GOVERN 6.2 | 8.5, 8.2.4 | Art. 15(2) | STA | PR.IP | — | LLM05 |
| P5.T9.6 Policy / Procedure Evolution | GOVERN 1.3, GOVERN 2.1 | 10.1 | Art. 9(9) | GRC | GV.OV | — | — |
| P5.T9.7 Emerging Threat Response | MANAGE 4.1, MEASURE 2.9 | 8.5 | Art. 9(9) | TVM | RS.IM | — | — |
| P5.T9.8 Capability Enhancements | MANAGE 4.1 | 8.5 | Art. 15(4) | AIS | PR.IP | — | — |
| P5.T9.9 Performance Optimization | MEASURE 2.6, MANAGE 4.1 | 8.5 | Art. 15(1) | AIS | PR.IP | — | — |
| P5.T9.10 Incident Lessons Learned | MANAGE 4.3, GOVERN 4.1 | 10.1 | Art. 62(2) | SEF | RS.IM | — | — |

#### Gap Filler Subtopics (v3.0)

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P5.T1.1 Agent Swarm Capability Evolution (GF1) | MANAGE 4.1 | 8.5 | Art. 15(4) | AIS | PR.IP | Agent subdomain | — |
| P5.T1.2 Supply Chain Provenance Control Evolution (GF3) | GOVERN 6.2 | 8.2.4, 10.1 | Art. 15(2) | STA | ID.SC | AML.T0002 | LLM05 |
| P5.T1.3 NHI Security Posture Evolution (GF4) | MANAGE 4.1 | 8.3.3, 10.1 | Art. 15(3) | IAM | PR.IP | — | — |
| P5.T1.4 Memory Poisoning Defense Evolution (GF5) | MANAGE 4.1, MEASURE 2.9 | 8.5 | Art. 15(4) | AIS | PR.IP | AML.T0000.001 | LLM03 |

### Topic 10: Educate (P5.T10)

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P5.T10.1 Operator Training Programs | GOVERN 4.1 | 7.2 | Art. 14(4-b) | HRS (Human Resources Security) | GV.AT | — | — |
| P5.T10.2 AI Security Awareness Training | GOVERN 4.1 | 7.3 | Art. 4(1) | HRS | GV.AT | — | — |
| P5.T10.3 Safe Prompt Engineering Education | GOVERN 4.1 | 7.2 | Art. 4(1) | HRS | GV.AT | — | LLM01 |
| P5.T10.4 Incident Response Drills | GOVERN 4.1, MANAGE 4.3 | 7.2, 8.4 | Art. 62(1) | SEF | RS.RP | — | — |
| P5.T10.5 Policy / Procedure Communication | GOVERN 2.1, GOVERN 4.1 | 7.3, 7.4 | Art. 17(1) | GRC | GV.AT | — | — |
| P5.T10.6 Industry Best Practices Sharing | GOVERN 5.2 | 7.3 | Art. 4(1) | GRC | GV.OC | — | — |
| P5.T10.7 Internal Documentation / Wikis | GOVERN 1.4 | 7.5 | Art. 11(1) | TRN | GV.AT | — | — |
| P5.T10.8 Vendor Security Training | GOVERN 6.2 | 7.2 | Art. 15(2) | STA | GV.AT | — | — |
| P5.T10.9 Role-Based Training | GOVERN 4.1 | 7.2 | Art. 4(1) | HRS | GV.AT | — | — |
| P5.T10.10 Culture / Accountability Framework | GOVERN 2.1, GOVERN 2.2 | 5.1, 7.3 | Art. 17(1-k) | GRC | GV.RR | — | — |

#### Gap Filler Subtopics (v3.0)

| AI SAFE2 Subtopic | NIST AI RMF | ISO 42001 | EU AI Act | CSA AICM Domain | NIST CSF 2.0 | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|---|
| P5.T2.1 Agent Operator / Swarm Manager Training (GF1) | GOVERN 4.1 | 7.2 | Art. 4(1) | HRS | GV.AT | Agent subdomain | — |
| P5.T2.2 NHI / Machine Identity Security Awareness (GF4) | GOVERN 4.1 | 7.3 | Art. 4(1) | HRS | GV.AT | — | — |
| P5.T2.3 Supply Chain / Model Security Culture (GF3) | GOVERN 4.1, GOVERN 6.2 | 7.3 | Art. 15(2) | STA, HRS | GV.AT | — | LLM05 |
| P5.T2.4 Memory Poisoning / Agent Security Awareness (GF5) | GOVERN 4.1 | 7.3 | Art. 4(1) | HRS | GV.AT | AML.T0000.001 | LLM03 |

---

## 7. Framework Coverage Summary

| Framework | AI SAFE2 v3.0 Coverage | Mapped Subcategories/Clauses |
|---|---|---|
| **NIST AI RMF 1.0** | 100% | All GOVERN, MAP, MEASURE, MANAGE subcategories |
| **ISO/IEC 42001:2022** | 100% | Clauses 5.x, 6.x, 7.x, 8.x, 9.x, 10.x |
| **EU AI Act** | 95%+ | Art. 4, 5, 9, 10, 11, 12, 13, 14, 15, 17, 60, 62 (high-risk) |
| **CSA AICM** | 90%+ | 16 of 18 domains mapped |
| **NIST CSF 2.0** | 100% | All 6 Functions (GV, ID, PR, DE, RS, RC) |
| **MITRE ATLAS** | 98% | 14 agent-specific + all legacy tactics |
| **OWASP Top 10 LLM** | 100% | LLM01–LLM10 |

---

## 8. References

1. NIST AI 100-1 (2023). AI Risk Management Framework 1.0.
2. ISO/IEC 42001:2022. AI Management System — Requirements.
3. EU AI Act (2024). Regulation (EU) 2024/1689 — Artificial Intelligence Act.
4. Cloud Security Alliance (2025). AI Controls Matrix (AICM) v1.0.
5. NIST CSF 2.0 (2024). Cybersecurity Framework 2.0.
6. MITRE ATLAS (2025). Adversarial Threat Landscape for AI Systems.
7. OWASP (2025). Top 10 for LLM Applications.
8. Cyber Strategy Institute (2025). AI SAFE2 Framework v3.0.

---

*© 2026 Cyber Strategy Institute. Licensed under CC BY 4.0.*
