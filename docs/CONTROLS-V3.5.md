# AI SAFE2 v3.5 control contracts

AI SAFE2 v3.5 normative requirements. Baseline v3.1 contains 161 controls. This revision retains those IDs and adds twelve controls, yielding 173. Existing component implementations retain their separately evidenced status. A requirement is an obligation on applicable deployments; source availability alone establishes no enforcement result.

Applicability must be recorded for the deployment, effect, actor and consequence. Each applicable child clause requires an identified enforcement or governance owner, test evidence, failure response and recovery procedure. Research-only clauses document unsettled measurements and do not impose a runtime threshold.

| Control | Name | Change |
| --- | --- | --- |
| [P1.T1.1](#p1-t1-1) | Input Validation & Schema Enforcement | RETAINED |
| [P1.T1.2](#p1-t1-2) | Malicious Prompt Filtering | RETAINED |
| [P1.T1.3](#p1-t1-3) | Data Quality Checks | RETAINED |
| [P1.T1.4](#p1-t1-4) | Toxic Content Detection | RETAINED |
| [P1.T1.5](#p1-t1-5) | Sensitive Data Masking (PII/PHI) | RETAINED |
| [P1.T1.6](#p1-t1-6) | Format Normalization | RETAINED |
| [P1.T1.7](#p1-t1-7) | Dependency Verification | RETAINED |
| [P1.T1.8](#p1-t1-8) | Encoding Validation | RETAINED |
| [P1.T1.9](#p1-t1-9) | Supply Chain Artifact Validation | RETAINED |
| [P1.T2.1](#p1-t2-1) | Agent Sandboxing | RETAINED |
| [P1.T2.2](#p1-t2-2) | Network Segmentation | RETAINED |
| [P1.T2.3](#p1-t2-3) | API Gateway Restrictions | RETAINED |
| [P1.T2.4](#p1-t2-4) | Model Versioning & Isolation | RETAINED |
| [P1.T2.5](#p1-t2-5) | Function Access Control | RETAINED |
| [P1.T2.6](#p1-t2-6) | Data Isolation | RETAINED |
| [P1.T2.7](#p1-t2-7) | Container Security | RETAINED |
| [P1.T2.8](#p1-t2-8) | Firewall Controls | RETAINED |
| [P1.T2.9](#p1-t2-9) | Credential Compartmentalization | RETAINED |
| [P1.T1.2_ADV](#p1-t1-2_adv) | Supply Chain Artifact Validation (OpenSSF OMS) | RETAINED |
| [P1.T1.4_ADV](#p1-t1-4_adv) | NHI Secret Validation | RETAINED |
| [P1.T1.5_ADV](#p1-t1-5_adv) | Memory-Specific Attack Mitigation | RETAINED |
| [P1.T2.1_ADV](#p1-t2-1_adv) | Multi-Agent Boundary Enforcement | RETAINED |
| [P1.T2.2_ADV](#p1-t2-2_adv) | NHI Access Control | RETAINED |
| [P1.T1.10](#p1-t1-10) | Indirect Injection Surface Coverage | RETAINED |
| [S1.3](#s1-3) | Semantic Isolation Boundary Enforcement | UPDATED |
| [S1.4](#s1-4) | Adversarial Input Fuzzing Pipeline | UPDATED |
| [S1.5](#s1-5) | Memory Governance Boundary Controls | UPDATED |
| [S1.6](#s1-6) | Cognitive Injection Sanitization | RETAINED |
| [S1.7](#s1-7) | No-Code / Low-Code Platform Security | RETAINED |
| [P2.T3.1](#p2-t3-1) | Real-Time Activity Logging | RETAINED |
| [P2.T3.2](#p2-t3-2) | Model Performance Monitoring | RETAINED |
| [P2.T3.3](#p2-t3-3) | Behavior Verification | RETAINED |
| [P2.T3.4](#p2-t3-4) | Explainability Tracking | RETAINED |
| [P2.T3.5](#p2-t3-5) | Bias & Fairness Monitoring | RETAINED |
| [P2.T3.6](#p2-t3-6) | Compliance Validation | RETAINED |
| [P2.T3.7](#p2-t3-7) | Decision Traceability | RETAINED |
| [P2.T3.8](#p2-t3-8) | User Interaction Logging | RETAINED |
| [P2.T3.9](#p2-t3-9) | Change Tracking | RETAINED |
| [P2.T3.10](#p2-t3-10) | Vulnerability Scanning | RETAINED |
| [P2.T4.1](#p2-t4-1) | AI System Registry | RETAINED |
| [P2.T4.2](#p2-t4-2) | Model Catalog | RETAINED |
| [P2.T4.3](#p2-t4-3) | Agent Capability Documentation | RETAINED |
| [P2.T4.4](#p2-t4-4) | Data Source Mapping | UPDATED |
| [P2.T4.5](#p2-t4-5) | API Inventory | RETAINED |
| [P2.T4.6](#p2-t4-6) | Tool Registry | RETAINED |
| [P2.T4.7](#p2-t4-7) | Dependency Tracking | RETAINED |
| [P2.T4.8](#p2-t4-8) | Architecture Documentation | RETAINED |
| [P2.T4.9](#p2-t4-9) | Risk Registers | RETAINED |
| [P2.T4.10](#p2-t4-10) | Configuration Baselines | RETAINED |
| [P2.T4.11](#p2-t4-11) | SBOM Generation | RETAINED |
| [P2.T1.1_ADV](#p2-t1-1_adv) | NHI Activity Logging | RETAINED |
| [P2.T1.2_ADV](#p2-t1-2_adv) | Agent Behavior Verification | RETAINED |
| [P2.T1.3_ADV](#p2-t1-3_adv) | Supply Chain Audit | RETAINED |
| [P2.T1.4_ADV](#p2-t1-4_adv) | Memory Poisoning Detection | RETAINED |
| [P2.T2.1_ADV](#p2-t2-1_adv) | NHI Registry | RETAINED |
| [P2.T2.2_ADV](#p2-t2-2_adv) | Agent Architecture Inventory | RETAINED |
| [A2.3](#a2-3) | Model Lineage Provenance Ledger | RETAINED |
| [A2.4](#a2-4) | Dynamic Agent State Inventory | RETAINED |
| [A2.5](#a2-5) | Semantic Execution Trace Logging | UPDATED |
| [A2.6](#a2-6) | RAG Corpus Diff Tracking | RETAINED |
| [P3.T5.1](#p3-t5-1) | Circuit Breakers | RETAINED |
| [P3.T5.2](#p3-t5-2) | Emergency Shutdown | RETAINED |
| [P3.T5.3](#p3-t5-3) | Fallback Mechanisms | RETAINED |
| [P3.T5.4](#p3-t5-4) | Error Handling | RETAINED |
| [P3.T5.5](#p3-t5-5) | Rate Limiting | RETAINED |
| [P3.T5.6](#p3-t5-6) | Rollback Procedures | RETAINED |
| [P3.T5.7](#p3-t5-7) | Kill Switches for Runaway Agents | RETAINED |
| [P3.T5.8](#p3-t5-8) | Blast Radius Containment | RETAINED |
| [P3.T5.9](#p3-t5-9) | Safe Defaults | RETAINED |
| [P3.T5.10](#p3-t5-10) | Incident Response | RETAINED |
| [P3.T6.1](#p3-t6-1) | Model Backups | RETAINED |
| [P3.T6.2](#p3-t6-2) | Data Recovery | RETAINED |
| [P3.T6.3](#p3-t6-3) | Backup Automation | RETAINED |
| [P3.T6.4](#p3-t6-4) | Disaster Recovery | RETAINED |
| [P3.T6.5](#p3-t6-5) | Business Continuity | RETAINED |
| [P3.T6.6](#p3-t6-6) | RTO/RPO Management | RETAINED |
| [P3.T6.7](#p3-t6-7) | Testing & Validation | RETAINED |
| [P3.T6.8](#p3-t6-8) | Off-Site Storage | RETAINED |
| [P3.T6.9](#p3-t6-9) | Configuration Restoration | RETAINED |
| [P3.T6.10](#p3-t6-10) | Incident Forensics | RETAINED |
| [P3.T1.1_ADV](#p3-t1-1_adv) | Distributed Agent Fail-Safe | RETAINED |
| [P3.T1.2_ADV](#p3-t1-2_adv) | NHI Revocation | RETAINED |
| [P3.T1.3_ADV](#p3-t1-3_adv) | Memory Poisoning Response | RETAINED |
| [P3.T2.1_ADV](#p3-t2-1_adv) | Agent State Recovery | RETAINED |
| [P3.T2.2_ADV](#p3-t2-2_adv) | NHI Credential Recovery | RETAINED |
| [F3.2](#f3-2) | Agent Recursion Limit Governor | RETAINED |
| [F3.3](#f3-3) | Swarm Quorum Abort Mechanism | UPDATED |
| [F3.4](#f3-4) | Behavioral Drift Baseline & Rollback | UPDATED |
| [F3.5](#f3-5) | Multi-Agent Cascade Containment | RETAINED |
| [P4.T7.1](#p4-t7-1) | Human Approval Workflows | RETAINED |
| [P4.T7.2](#p4-t7-2) | Explainability | RETAINED |
| [P4.T7.3](#p4-t7-3) | Interactive Feedback | RETAINED |
| [P4.T7.4](#p4-t7-4) | Escalation Procedures | RETAINED |
| [P4.T7.5](#p4-t7-5) | Real-Time Intervention | RETAINED |
| [P4.T7.6](#p4-t7-6) | User Interaction Oversight | RETAINED |
| [P4.T7.7](#p4-t7-7) | Red Teaming | RETAINED |
| [P4.T7.8](#p4-t7-8) | Risk Acceptance | RETAINED |
| [P4.T7.9](#p4-t7-9) | Collaboration Tools | RETAINED |
| [P4.T7.10](#p4-t7-10) | Transparency Reporting | UPDATED |
| [P4.T8.1](#p4-t8-1) | Performance Dashboards | RETAINED |
| [P4.T8.2](#p4-t8-2) | Anomaly Detection | RETAINED |
| [P4.T8.3](#p4-t8-3) | Security Logging | RETAINED |
| [P4.T8.4](#p4-t8-4) | Accuracy & Drift Monitoring | RETAINED |
| [P4.T8.5](#p4-t8-5) | Cost Tracking | RETAINED |
| [P4.T8.6](#p4-t8-6) | Latency Metrics | RETAINED |
| [P4.T8.7](#p4-t8-7) | Error Tracking | RETAINED |
| [P4.T8.8](#p4-t8-8) | API Quota Monitoring | RETAINED |
| [P4.T8.9](#p4-t8-9) | Data Quality Monitoring | RETAINED |
| [P4.T8.10](#p4-t8-10) | Compliance Logs | RETAINED |
| [P4.T1.1_ADV](#p4-t1-1_adv) | Multi-Agent Approval | RETAINED |
| [P4.T1.2_ADV](#p4-t1-2_adv) | NHI Privilege Review | RETAINED |
| [P4.T2.1_ADV](#p4-t2-1_adv) | Distributed Agent Monitoring | RETAINED |
| [P4.T2.2_ADV](#p4-t2-2_adv) | NHI Monitoring | RETAINED |
| [P4.T2.3_ADV](#p4-t2-3_adv) | Memory Poisoning Monitor | RETAINED |
| [M4.4](#m4-4) | Adversarial Behavior Detection Pipeline | RETAINED |
| [M4.5](#m4-5) | Tool-Misuse Detection Controls | RETAINED |
| [M4.6](#m4-6) | Emergent Behavior Anomaly Detection | RETAINED |
| [M4.7](#m4-7) | Jailbreak & Injection Telemetry Layer | RETAINED |
| [M4.8](#m4-8) | Cloud AI Platform-Specific Monitoring | RETAINED |
| [P5.T9.1](#p5-t9-1) | Threat Intel Integration | RETAINED |
| [P5.T9.2](#p5-t9-2) | Playbook Updates | RETAINED |
| [P5.T9.3](#p5-t9-3) | Model Retraining | RETAINED |
| [P5.T9.4](#p5-t9-4) | Patch Management | RETAINED |
| [P5.T9.5](#p5-t9-5) | Dependency Remediation | RETAINED |
| [P5.T9.6](#p5-t9-6) | Policy Evolution | RETAINED |
| [P5.T9.7](#p5-t9-7) | Emerging Threats | RETAINED |
| [P5.T9.8](#p5-t9-8) | Capability Enhancements | RETAINED |
| [P5.T9.9](#p5-t9-9) | Performance Optimization | RETAINED |
| [P5.T9.10](#p5-t9-10) | Lessons Learned | RETAINED |
| [P5.T10.1](#p5-t10-1) | Operator Training | UPDATED |
| [P5.T10.2](#p5-t10-2) | Security Awareness | RETAINED |
| [P5.T10.3](#p5-t10-3) | Safe Prompting | RETAINED |
| [P5.T10.4](#p5-t10-4) | Incident Drills | RETAINED |
| [P5.T10.5](#p5-t10-5) | Policy Communication | RETAINED |
| [P5.T10.6](#p5-t10-6) | Industry Sharing | RETAINED |
| [P5.T10.7](#p5-t10-7) | Internal Documentation | RETAINED |
| [P5.T10.8](#p5-t10-8) | Vendor Training | RETAINED |
| [P5.T10.9](#p5-t10-9) | Role-Based Training | RETAINED |
| [P5.T10.10](#p5-t10-10) | Culture | RETAINED |
| [P5.T1.1_ADV](#p5-t1-1_adv) | Swarm Evolution | RETAINED |
| [P5.T1.2_ADV](#p5-t1-2_adv) | Supply Chain Evolution | RETAINED |
| [P5.T1.3_ADV](#p5-t1-3_adv) | NHI Posture | RETAINED |
| [P5.T1.4_ADV](#p5-t1-4_adv) | Memory Defense Evolution | RETAINED |
| [P5.T2.1_ADV](#p5-t2-1_adv) | Swarm Training | RETAINED |
| [P5.T2.2_ADV](#p5-t2-2_adv) | NHI Awareness | RETAINED |
| [P5.T2.3_ADV](#p5-t2-3_adv) | Supply Chain Culture | RETAINED |
| [P5.T2.4_ADV](#p5-t2-4_adv) | Memory Awareness | RETAINED |
| [E5.1](#e5-1) | Continuous Adversarial Evaluation Cadence | UPDATED |
| [E5.2](#e5-2) | Capability Emergence Review Process | UPDATED |
| [E5.3](#e5-3) | Evaluation-Safe Pattern Library | RETAINED |
| [E5.4](#e5-4) | Red-Team Artifact Repository | RETAINED |
| [S1.8](#s1-8) | Pre-Trust Initialization Boundary | NEW |
| [F3.6](#f3-6) | Aggregate Consumable-Authority Ceiling | NEW |
| [F3.7](#f3-7) | Environment Binding and Assertion | NEW |
| [A2.7](#a2-7) | Idempotency and Side-Effect Ledger | NEW |
| [A2.8](#a2-8) | Verified Outcome Contract | NEW |
| [E5.5](#e5-5) | Declared Success Criteria Gate | NEW |
| [A2.9](#a2-9) | Evidence-Based Failure Attribution | NEW |
| [CP.1](#cp-1) | Agent Failure Mode Taxonomy | RETAINED |
| [CP.2](#cp-2) | Adversarial ML Threat Model Integration | RETAINED |
| [CP.3](#cp-3) | ACT Capability Tiers 1-4 | UPDATED |
| [CP.4](#cp-4) | Agentic Control Plane Governance | UPDATED |
| [CP.5](#cp-5) | Platform-Specific Agent Security Profiles | UPDATED |
| [CP.6](#cp-6) | AI Incident Feedback Loop Integration | UPDATED |
| [CP.7](#cp-7) | Deception & Active Defense Layer | RETAINED |
| [CP.8](#cp-8) | Catastrophic Risk Threshold Controls | UPDATED |
| [CP.9](#cp-9) | Agent Replication Governance (ARG) | UPDATED |
| [CP.10](#cp-10) | HEAR Doctrine (Human Ethical Agent of Record) | UPDATED |
| [CP.11](#cp-11) | Trust Lifecycle Governance | NEW |
| [CP.12](#cp-12) | Final-Effect Authorization | NEW |
| [CP.13](#cp-13) | Control Evidence Independence | NEW |
| [CP.14](#cp-14) | Organizational AI Management Governance | NEW |
| [CP.15](#cp-15) | Design-Time Coordination Contract | NEW |

<a id="p1-t1-1"></a>

## P1.T1.1 Input Validation & Schema Enforcement

Validate inputs against schemas; reject malformed formats; enforce type checking and content-length restrictions.

<a id="p1-t1-2"></a>

## P1.T1.2 Malicious Prompt Filtering

Detect and block prompt injection (OWASP LLM01); implement adversarial detection; monitor for jailbreaks.

<a id="p1-t1-3"></a>

## P1.T1.3 Data Quality Checks

Validate data integrity; detect statistical anomalies and outliers; flag corrupted data.

<a id="p1-t1-4"></a>

## P1.T1.4 Toxic Content Detection

Screen for harmful content; implement toxicity scoring; filter based on policy.

<a id="p1-t1-5"></a>

## P1.T1.5 Sensitive Data Masking (PII/PHI)

Auto-detect and mask PII; redact PHI (HIPAA); implement DLP controls; tokenize sensitive fields.

<a id="p1-t1-6"></a>

## P1.T1.6 Format Normalization

Standardize input formats; validate character encodings (UTF-8); prevent encoding attacks.

<a id="p1-t1-7"></a>

## P1.T1.7 Dependency Verification

Validate software dependencies; maintain SBOMs; cross-reference CVE databases.

<a id="p1-t1-8"></a>

## P1.T1.8 Encoding Validation

Enforce normalization forms (NFKC); prevent homoglyph and encoding-based attacks.

<a id="p1-t1-9"></a>

## P1.T1.9 Supply Chain Artifact Validation

Cryptographically verify model and dataset authenticity; validate checksums (SHA-256); enforce signature verification.

<a id="p1-t2-1"></a>

## P1.T2.1 Agent Sandboxing

Deploy agents in isolated environments; implement resource limits (CPU/RAM); use containerization.

<a id="p1-t2-2"></a>

## P1.T2.2 Network Segmentation

Isolate AI workloads in dedicated VLANs; use firewalls and ACLs to restrict traffic.

<a id="p1-t2-3"></a>

## P1.T2.3 API Gateway Restrictions

Deploy gateways with auth; implement rate limiting; restrict access by IP/Role.

<a id="p1-t2-4"></a>

## P1.T2.4 Model Versioning & Isolation

Maintain separate environments for model versions; isolate production from development; prevent unintended rollbacks.

<a id="p1-t2-5"></a>

## P1.T2.5 Function Access Control

Restrict agent access to tools; implement whitelisting; use least privilege.

<a id="p1-t2-6"></a>

## P1.T2.6 Data Isolation

Separate sensitive data; implement access controls; encrypt at rest and in transit.

<a id="p1-t2-7"></a>

## P1.T2.7 Container Security

Harden container images (minimal base); scan for vulnerabilities; implement runtime monitoring.

<a id="p1-t2-8"></a>

## P1.T2.8 Firewall Controls

Deploy NGFWs; implement IDS/IPS; enforce egress filtering.

<a id="p1-t2-9"></a>

## P1.T2.9 Credential Compartmentalization

Store API keys in secure vaults (HashiCorp/AWS); rotate regularly; never in code or prompts.

<a id="p1-t1-2_adv"></a>

## P1.T1.2_ADV Supply Chain Artifact Validation (OpenSSF OMS)

Cryptographic model verification using Sigstore/Cosign; SBOM validation; provenance chain; SHA-256 model fingerprinting.

<a id="p1-t1-4_adv"></a>

## P1.T1.4_ADV NHI Secret Validation

Detect embedded credentials/tokens in AI outputs; GitGuardian integration for real-time secret detection.

<a id="p1-t1-5_adv"></a>

## P1.T1.5_ADV Memory-Specific Attack Mitigation

Cryptographic memory fingerprinting; thread injection prevention; semantic similarity analysis for gradual RAG poison.

<a id="p1-t2-1_adv"></a>

## P1.T2.1_ADV Multi-Agent Boundary Enforcement

Isolate Agent-to-Agent communications; auto-quarantine anomalous agents; P2P trust scoring.

<a id="p1-t2-2_adv"></a>

## P1.T2.2_ADV NHI Access Control

Catalog all service accounts and agents; assign minimum permissions to NHI entities; automated decommissioning.

<a id="p1-t1-10"></a>

## P1.T1.10 Indirect Injection Surface Coverage

Enumerate every non-prompt input channel the agent processes and apply the same sanitization rigor as direct user input.

<a id="s1-3"></a>

## S1.3 Semantic Isolation Boundary Enforcement

Architecturally separate trusted system instruction context from untrusted content processing at the inference layer.

### C12 inherited requirement detail

Message, shared artifact and tool result provenance use common trust rules. A new top-level family could obscure cross-agent differences in custody and authority.

**Source and research** Evidence waves 01-06; C12 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/036_v35_c12.md)

- **S1.3.R01** (Requirement) Preserve provenance, authority scope, expiry and trust classification across agent messages, plans, files, approvals and logs.
- **S1.3.R02** (Requirement) Prevent agent-to-agent handoffs and shared-source agreement from silently establishing authorization or independent corroboration.

**Acceptance and failure analysis** Inter-agent artifact governance and synthetic consensus. Compare direct messages, shared state and multiple derivatives of one source.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="s1-4"></a>

## S1.4 Adversarial Input Fuzzing Pipeline

Integrate automated adversarial testing into CI/CD - systematic attack probe battery before every model update and deployment.

### C15 inherited requirement detail

The existing ingestion and destination boundaries apply. Add modality-specific handling and destination validation. A profile is useful only where the deployment requires different rules.

**Source and research** Evidence waves 01-06; C15 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/039_v35_c15.md)

- **S1.4.R01** (Requirement) Cover every enabled modality, including OCR, images, metadata, audio, markup and encoded content.
- **S1.4.R02** (Requirement) Validate generated commands, SQL, URLs, paths and tool arguments against the destination boundary before execution.

**Acceptance and failure analysis** Multimodal ingestion and generated-output consumption. Record supported formats and verify safe handling of each enabled path.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="s1-5"></a>

## S1.5 Memory Governance Boundary Controls

Every write to persistent agent memory requires authorization, sanitization with input-equivalent rigor, and an append-only audit log entry.

### C13 inherited requirement detail

Existing memory governance needs provenance, permitted use, tenancy, expiry, derivative tracking and clean restores. Separate controls for every memory representation fragment the policy.

**Source and research** Evidence waves 01-06; C13 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/037_v35_c13.md)

- **S1.5.R01** (Requirement) Assign memory provenance, permitted uses, tenant/purpose scope, owner and expiry at admission.
- **S1.5.R02** (Requirement) Quarantine instruction-bearing untrusted entries and propagate invalidation to derived state, replicas, exports and restores.

**Acceptance and failure analysis** Persistent-state transformations. Verify scope and invalidation after summarization, export, cache and restoration.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C39 inherited requirement detail

Expiry and provenance describe origin and lifetime. They do not establish whether an entry is failed or superseded. Reuse the memory lifecycle while making validity independently queryable. Incorrect corrections can suppress useful knowledge.

**Source and research** Wave 04 Holds, Memory Outcome Annotation; Wave 02 derived-state laundering

[Research decision](../research/063_v35_c39.md)

- **S1.5.R03** (Requirement) Attach verified, failed, disputed, superseded or unknown outcome status to reusable artifacts and durable entries.
- **S1.5.R04** (Requirement) Preserve correction links, original evidence and reason for status changes.
- **S1.5.R05** (Requirement) Retrieval must surface an applicable correction with the original claim and block superseded instructions from silently regaining authority.
- **S1.5.R06** (Requirement) Carry correction state through summarization, export, replica restore and derivative generation.

**Acceptance and failure analysis** Poison a synthetic entry, correct it, then retrieve its summary and restore its backup. Test erroneous correction reversal with accountable review.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="s1-6"></a>

## S1.6 Cognitive Injection Sanitization

Semantic intent analysis layer that detects multi-turn behavioral conditioning, role confusion, and few-shot pattern implanting beyond pattern-matching filters.

<a id="s1-7"></a>

## S1.7 No-Code / Low-Code Platform Security

First dedicated governance standard for no-code AI workflow platforms: sandbox isolation, credential scoping, template supply chain, CVE patching as P1.

<a id="p2-t3-1"></a>

## P2.T3.1 Real-Time Activity Logging

Log all activities with timestamps; capture prompts and API calls; ensure tamper-proof storage.

<a id="p2-t3-2"></a>

## P2.T3.2 Model Performance Monitoring

Monitor accuracy and precision; detect data and concept drift.

<a id="p2-t3-3"></a>

## P2.T3.3 Behavior Verification

Establish baselines; detect deviations and anomalies; flag unusual patterns.

<a id="p2-t3-4"></a>

## P2.T3.4 Explainability Tracking

Log decisions (SHAP/LIME); track reasoning paths; enable post-hoc analysis.

<a id="p2-t3-5"></a>

## P2.T3.5 Bias & Fairness Monitoring

Measure bias across demographics; track fairness metrics; detect discrimination.

<a id="p2-t3-6"></a>

## P2.T3.6 Compliance Validation

Map controls to SOC2/ISO/NIST; track implementation; conduct periodic audits.

<a id="p2-t3-7"></a>

## P2.T3.7 Decision Traceability

Track provenance from input to output; document data sources; maintain chain of custody.

<a id="p2-t3-8"></a>

## P2.T3.8 User Interaction Logging

Log prompts and feedback; track satisfaction metrics; analyze behavior.

<a id="p2-t3-9"></a>

## P2.T3.9 Change Tracking

Log configuration changes; track model updates and retraining; version control artifacts.

<a id="p2-t3-10"></a>

## P2.T3.10 Vulnerability Scanning

Conduct regular scans; assess threats (MITRE ATLAS); correlate with CVEs.

<a id="p2-t4-1"></a>

## P2.T4.1 AI System Registry

Catalog all LLMs, RAGs, and Agents; document owners and criticality.

<a id="p2-t4-2"></a>

## P2.T4.2 Model Catalog

Inventory base and fine-tuned models; track versions and training sets.

<a id="p2-t4-3"></a>

## P2.T4.3 Agent Capability Documentation

Document agent autonomy levels, tools, and decision authority.

<a id="p2-t4-4"></a>

## P2.T4.4 Data Source Mapping

Map data lineage; track refresh rates; identify RAG dependencies.

### C53 inherited requirement detail

Data Source Mapping already owns external-source identity and inventory. Add purpose, declaration, freshness and correction detail here, with CP.14 policy ownership. A new top-level rights control would duplicate source inventory and could imply legal authority. This placement accepts provider-neutral observations while preserving the separate permission decision. More metadata increases collection burden; minimize it and record unknowns.

**Source and research** Repository issue #390, provider-neutral source-rights observation proposal. The named AcqPath service is attributed context, not a required provider or independently verified integration.

[Research decision](../research/077_v35_c53.md)

- **P2.T4.4.R1** (Requirement) Record the externally sourced resource identifier, intended use, declaration state, observation time and freshness, provenance and integrity evidence before downstream policy evaluation.
- **P2.T4.4.R2** (Requirement) Keep the observation provider-neutral and distinguish observed declarations from licences, ownership, actual use and permission. UNKNOWN, stale or contradictory declarations cannot become permission by default.
- **P2.T4.4.R3** (Requirement) Bind reuse to the purpose and policy decision; record review/correction paths, minimization and unresolved rights or provenance conflicts without bypassing source access controls.

**Acceptance and failure analysis** Test missing purpose, UNKNOWN, stale and conflicting declarations; preserve them as unresolved inputs and refuse a policy decision that treats them as permission. Verify the observation does not grant a licence, establish ownership, prove use or bypass access controls. Test a corrected declaration and a permitted purpose with separately recorded policy authority.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="p2-t4-5"></a>

## P2.T4.5 API Inventory

Catalog all APIs and MCP endpoints; document auth methods and rate limits.

<a id="p2-t4-6"></a>

## P2.T4.6 Tool Registry

Maintain registry of tools and plugins; track permissions and usage.

<a id="p2-t4-7"></a>

## P2.T4.7 Dependency Tracking

Track libraries and frameworks; identify transitive dependencies; cross-reference CVEs.

<a id="p2-t4-8"></a>

## P2.T4.8 Architecture Documentation

Document RAG and MCP architectures and data flows.

<a id="p2-t4-9"></a>

## P2.T4.9 Risk Registers

Centralized threat register; link risks to components; track mitigation.

<a id="p2-t4-10"></a>

## P2.T4.10 Configuration Baselines

Establish baselines; track deviations; drift detection.

<a id="p2-t4-11"></a>

## P2.T4.11 SBOM Generation

Generate SBOMs for all models and applications; correlate with CVEs.

<a id="p2-t1-1_adv"></a>

## P2.T1.1_ADV NHI Activity Logging

Log all actions by service accounts and agents; track credential usage; SIEM integration.

<a id="p2-t1-2_adv"></a>

## P2.T1.2_ADV Agent Behavior Verification

Verify multi-agent voting mechanisms; track memory state across interactions; SHA-256 state hashing.

<a id="p2-t1-3_adv"></a>

## P2.T1.3_ADV Supply Chain Audit

Verify OpenSSF OMS signatures; validate SBOM completeness against actual dependencies.

<a id="p2-t1-4_adv"></a>

## P2.T1.4_ADV Memory Poisoning Detection

Audit knowledge bases for poisoned content; detect adversarial trigger phrases.

<a id="p2-t2-1_adv"></a>

## P2.T2.1_ADV NHI Registry

Automated discovery of NHI; lifecycle tracking from creation to decommissioning; fingerprinting.

<a id="p2-t2-2_adv"></a>

## P2.T2.2_ADV Agent Architecture Inventory

Document multi-agent communication patterns; track orchestration frameworks.

<a id="a2-3"></a>

## A2.3 Model Lineage Provenance Ledger

Cryptographic chain of custody from base model through every fine-tuning stage to production; extends OpenSSF OMS.

<a id="a2-4"></a>

## A2.4 Dynamic Agent State Inventory

Real-time registry of every deployed agent with owner_of_record, ACT tier, tool authorizations, hear_agent_of_record, and control_plane_id.

<a id="a2-5"></a>

## A2.5 Semantic Execution Trace Logging

Captures full agent execution trace: reasoning chain, every tool call with parameters, every memory operation - written to an append-only store the agent cannot modify.

### C21 inherited requirement detail

Existing evidence ownership avoids a parallel ledger. Add access, retention, dependency coverage, and explicit suitability assessment. Privacy and completeness can conflict.

**Source and research** Evidence waves 01-06; C21 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/045_v35_c21.md)

- **A2.5.R01** (Requirement) Inventory models, data, routes, skills, policy bundles, tools, evaluators and their deployment dependencies.
- **A2.5.R02** (Requirement) Minimize evidence content, bound access and retention, and preserve sufficient scope for reconstruction.

**Acceptance and failure analysis** Evidence custody and reproducibility. Verify reconstruction using minimized records and distinguish signed origin from suitability.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C45 inherited requirement detail

A source declaration does not resolve training rights, downstream reuse or a conflict between deletion and evidence retention. Add lifecycle-specific decisions and accountable conflict routing. This needs specialist applicability review.

**Source and research** Wave 02 IP/data rights and conflicting obligations; Wave 05 #390 and C11 redress

[Research decision](../research/069_v35_c45.md)

- **A2.5.R03** (Requirement) Distinguish rights and policy decisions for training, retrieval, generation, publication and downstream reuse.
- **A2.5.R04** (Requirement) Record declaration freshness, conflicting evidence and uncertainty without inferring permission from UNKNOWN.
- **A2.5.R05** (Requirement) Route deletion, retention, security evidence and transparency conflicts to an accountable decision maker.
- **A2.5.R06** (Requirement) Propagate approved correction/deletion decisions to applicable derived stores and record justified retention exceptions.

**Acceptance and failure analysis** Test contradictory declarations, a deletion request with a legitimate hold, and expired reuse permission. Report applicable scope and unresolved legal questions.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C52 inherited requirement detail

Discoverability without precise contracts leaves agents guessing which version and evidence apply. Extend existing CLI/manifest ownership. A new interface must preserve schema compatibility and avoid granting decision authority.

**Source and research** Wave 02 retrieval interfaces; Wave 04 diagnosis; recovery files

[Research decision](../research/076_v35_c52.md)

- **A2.5.R07** (Requirement) Return canonical IDs, source revision, applicability, parent inheritance and evidence status in machine queries.
- **A2.5.R08** (Requirement) Link each requirement to a test or declared verification gap and a supported repair or recovery path.
- **A2.5.R09** (Requirement) Prevent ambiguous aliases and inferred crosswalk chains from producing authoritative compliance answers.
- **A2.5.R10** (Requirement) Bind output to the assessed system and retain explicit unknown, partial, stale and unsupported states.

**Acceptance and failure analysis** Run a synthetic agent workflow that queries a requirement, applies a bounded fix and rechecks the failing test. Test stale editions, ambiguous aliases and a missing enforcement implementation.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="a2-6"></a>

## A2.6 RAG Corpus Diff Tracking

Hash-verified change log for the retrieval layer; correlates behavioral changes to corpus changes automatically.

<a id="p3-t5-1"></a>

## P3.T5.1 Circuit Breakers

Implement circuit breakers to prevent cascading failures; design graceful degradation.

<a id="p3-t5-2"></a>

## P3.T5.2 Emergency Shutdown

Define protocols for runaway agents; implement operator kill switches.

<a id="p3-t5-3"></a>

## P3.T5.3 Fallback Mechanisms

Design failover strategies; implement redundant systems.

<a id="p3-t5-4"></a>

## P3.T5.4 Error Handling

Robust error handling in pipelines; fail-closed vs fail-open policies.

<a id="p3-t5-5"></a>

## P3.T5.5 Rate Limiting

Prevent resource exhaustion; throttle API calls and agent actions.

<a id="p3-t5-6"></a>

## P3.T5.6 Rollback Procedures

Version control for artifacts; define rollback criteria.

<a id="p3-t5-7"></a>

## P3.T5.7 Kill Switches for Runaway Agents

Implement kill switches with tiered authorization to halt agent execution.

<a id="p3-t5-8"></a>

## P3.T5.8 Blast Radius Containment

Compartmentalize systems; define containment zones.

<a id="p3-t5-9"></a>

## P3.T5.9 Safe Defaults

Design safe behaviors; validate assumptions; fail securely.

<a id="p3-t5-10"></a>

## P3.T5.10 Incident Response

Develop AI-specific playbooks; define escalation paths.

<a id="p3-t6-1"></a>

## P3.T6.1 Model Backups

Regular backups of models and states; geo-diverse storage.

<a id="p3-t6-2"></a>

## P3.T6.2 Data Recovery

Procedures for AI datasets; point-in-time recovery.

<a id="p3-t6-3"></a>

## P3.T6.3 Backup Automation

Automate backup processes; monitor success and failure.

<a id="p3-t6-4"></a>

## P3.T6.4 Disaster Recovery

Develop plans; define priorities; conduct drills.

<a id="p3-t6-5"></a>

## P3.T6.5 Business Continuity

Integrate AI into BCP; define minimum viable services.

<a id="p3-t6-6"></a>

## P3.T6.6 RTO/RPO Management

Define objectives; monitor achievement.

<a id="p3-t6-7"></a>

## P3.T6.7 Testing & Validation

Regular recovery tests; validate backup integrity.

<a id="p3-t6-8"></a>

## P3.T6.8 Off-Site Storage

Encrypted off-site backups.

<a id="p3-t6-9"></a>

## P3.T6.9 Configuration Restoration

Backup IaC; version control configs.

<a id="p3-t6-10"></a>

## P3.T6.10 Incident Forensics

Forensic analysis; root cause; blameless post-mortems.

<a id="p3-t1-1_adv"></a>

## P3.T1.1_ADV Distributed Agent Fail-Safe

Centralized kill switch for multi-agent systems; auto-quarantine of malicious agents; cascading failure prevention.

<a id="p3-t1-2_adv"></a>

## P3.T1.2_ADV NHI Revocation

Automated credential rotation; immediate emergency disabling of service accounts.

<a id="p3-t1-3_adv"></a>

## P3.T1.3_ADV Memory Poisoning Response

Real-time alerts on RAG contamination; agent quarantine; compromised source isolation.

<a id="p3-t2-1_adv"></a>

## P3.T2.1_ADV Agent State Recovery

Point-in-time snapshots of agent memory; version control for vector DBs.

<a id="p3-t2-2_adv"></a>

## P3.T2.2_ADV NHI Credential Recovery

Secure escrow mechanisms for credentials; HSM integration for key protection.

<a id="f3-2"></a>

## F3.2 Agent Recursion Limit Governor

Hard cap on tool-calling depth enforced at the API gateway layer - not the system prompt. Default maximum 4. Fail-closed.

<a id="f3-3"></a>

## F3.3 Swarm Quorum Abort Mechanism

Decentralized threshold-based abort: when a configurable quorum of swarm agents agree the task should stop, coordinated shutdown proceeds without a centralized kill signal.

### C23 inherited requirement detail

Existing abort governance already owns voting. Add correlated evidence and membership tests, while keeping emergency stop independently exercisable. Quorum can harm availability if misapplied.

**Source and research** Evidence waves 01-06; C23 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/047_v35_c23.md)

- **F3.3.R01** (Requirement) Define membership and independence for quorum decisions, including source overlap and common-model failure.
- **F3.3.R02** (Requirement) Prevent an agent from manufacturing approval through spawned votes; retain an independent emergency stop.

**Acceptance and failure analysis** Correlated judgment and shared sources. Measure independence and behavior under partial participation.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="f3-4"></a>

## F3.4 Behavioral Drift Baseline & Rollback

Establish measurable behavioral baselines with defined probe sets; automated rollback when drift exceeds configurable thresholds.

### C17 inherited requirement detail

Recovery owns fallback and reconstruction. Pin actual routing, preserve policy, and declare degraded capabilities. Wider fallback improves resilience but enlarges the trusted estate.

**Source and research** Evidence waves 01-06; C17 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/041_v35_c17.md)

- **F3.4.R01** (Requirement) Record actual model/provider/route identities and verify that fallback preserves applicable policy and authority.
- **F3.4.R02** (Requirement) Reassess material substitutions and exercise approved degraded operation without uncontrolled endpoint replacement.

**Acceptance and failure analysis** Model retirement, routing drift and degraded operation. Verify outage handling and version-change requalification.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="f3-5"></a>

## F3.5 Multi-Agent Cascade Containment

Limits the blast radius of agent failures in pipeline and orchestrator architectures; failed agents isolated so downstream agents receive clean error signals.

<a id="p4-t7-1"></a>

## P4.T7.1 Human Approval Workflows

HITL for high-risk decisions; define approval authorities.

<a id="p4-t7-2"></a>

## P4.T7.2 Explainability

Provide reasoning chains; implement interpretability techniques.

<a id="p4-t7-3"></a>

## P4.T7.3 Interactive Feedback

RLHF loops; track feedback metrics.

<a id="p4-t7-4"></a>

## P4.T7.4 Escalation Procedures

Route alerts based on severity; integrate with incident management.

<a id="p4-t7-5"></a>

## P4.T7.5 Real-Time Intervention

Enable override controls; provide visibility dashboards.

<a id="p4-t7-6"></a>

## P4.T7.6 User Interaction Oversight

Monitor for abuse and malice; track trust metrics.

<a id="p4-t7-7"></a>

## P4.T7.7 Red Teaming

Regular adversarial testing; validate security controls.

<a id="p4-t7-8"></a>

## P4.T7.8 Risk Acceptance

Establish acceptance procedures; document compensating controls.

<a id="p4-t7-9"></a>

## P4.T7.9 Collaboration Tools

Shared dashboards for Governance, Security, and Engineering.

<a id="p4-t7-10"></a>

## P4.T7.10 Transparency Reporting

Report incidents and risks to stakeholders.

### C19 inherited requirement detail

Transparency and affected-party intervention belong together, with explicit distinction between operator stop and affected-person redress. A new disclosure standard would need a different audience or authority.

**Source and research** Evidence waves 01-06; C19 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/043_v35_c19.md)

- **P4.T7.10.R01** (Requirement) Provide proportionate notice, accessible contestation, accountable review and correction or remedy for consequential effects.
- **P4.T7.10.R02** (Requirement) Record the observed remedy separately from the operator stop and from a tool-reported success.

**Acceptance and failure analysis** Disclosure and remedy. Test accessible notice, accountable review, correction and actual remedy without relying on the original automated decision.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C46 inherited requirement detail

Operator approval leaves bystanders, workers and affected populations unrepresented. Expand existing impact and remedy requirements with an explicit route for their evidence. Participation can raise privacy and representativeness problems.

**Source and research** Wave 02 worker/public participation; Wave 06 rubric contestability

[Research decision](../research/070_v35_c46.md)

- **P4.T7.10.R03** (Requirement) Identify affected people absent from the operator approval chain.
- **P4.T7.10.R04** (Requirement) Collect proportionate input on impacts and accessibility and disclose its limitations.
- **P4.T7.10.R05** (Requirement) Provide an accessible route to challenge, correct or escalate material effects.
- **P4.T7.10.R06** (Requirement) Record whether input changed design, deployment, restrictions or remedy.

**Acceptance and failure analysis** Trace a complaint from a non-user through accountable review to an observed correction, retaining disagreement and safety constraints.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="p4-t8-1"></a>

## P4.T8.1 Performance Dashboards

Real-time monitoring; visualize KPIs and trends.

<a id="p4-t8-2"></a>

## P4.T8.2 Anomaly Detection

ML-based detection of unusual patterns; tune thresholds.

<a id="p4-t8-3"></a>

## P4.T8.3 Security Logging

Log security events; forward to SIEM; correlate events.

<a id="p4-t8-4"></a>

## P4.T8.4 Accuracy & Drift Monitoring

Monitor model performance; detect concept drift.

<a id="p4-t8-5"></a>

## P4.T8.5 Cost Tracking

Monitor token consumption and budget quotas.

<a id="p4-t8-6"></a>

## P4.T8.6 Latency Metrics

Track response times and throughput.

<a id="p4-t8-7"></a>

## P4.T8.7 Error Tracking

Categorize failure modes; automate remediation.

<a id="p4-t8-8"></a>

## P4.T8.8 API Quota Monitoring

Monitor call volumes; alert on exhaustion and abuse.

<a id="p4-t8-9"></a>

## P4.T8.9 Data Quality Monitoring

Monitor input quality; detect degradation.

<a id="p4-t8-10"></a>

## P4.T8.10 Compliance Logs

Maintain specific logs for regulatory audits.

<a id="p4-t1-1_adv"></a>

## P4.T1.1_ADV Multi-Agent Approval

Human review when agents disagree; human gate for financial and system-level actions.

<a id="p4-t1-2_adv"></a>

## P4.T1.2_ADV NHI Privilege Review

JIT access for temporary privilege elevation; baseline validation for requests.

<a id="p4-t2-1_adv"></a>

## P4.T2.1_ADV Distributed Agent Monitoring

Monitor availability and responsiveness of agents; track swarm topology and agreement rates.

<a id="p4-t2-2_adv"></a>

## P4.T2.2_ADV NHI Monitoring

Real-time NHI activity dashboard; detect unusual API call patterns and geo-location anomalies.

<a id="p4-t2-3_adv"></a>

## P4.T2.3_ADV Memory Poisoning Monitor

Monitor RAG source integrity; detect embedding drift toward adversarial regions.

<a id="m4-4"></a>

## M4.4 Adversarial Behavior Detection Pipeline

Continuously probes deployed agents with adversarial inputs and monitors behavioral responses; attack patterns from red-team repository feed detection rules automatically.

<a id="m4-5"></a>

## M4.5 Tool-Misuse Detection Controls

Establishes tool invocation baselines; detects tool squatting, unexpected tool calls, anomalous parameters, and invocation frequency spikes.

<a id="m4-6"></a>

## M4.6 Emergent Behavior Anomaly Detection

Classifies behavioral novelty - new task types, unexpected tool sequences, systematic decision bias - as security-relevant signals requiring governance review.

<a id="m4-7"></a>

## M4.7 Jailbreak & Injection Telemetry Layer

Unified logging and classification for all jailbreak attempts by technique: direct injection, indirect injection, cognitive injection, encoding bypass. Feeds E5.4 artifact repository.

<a id="m4-8"></a>

## M4.8 Cloud AI Platform-Specific Monitoring

Monitors Bedrock UpdateGuardrail and UpdateDataSource APIs; Azure AI Foundry configuration changes; platform attack paths that standard CloudTrail monitoring misses.

<a id="p5-t9-1"></a>

## P5.T9.1 Threat Intel Integration

Integrate CVE and MITRE feeds; update threat models.

<a id="p5-t9-2"></a>

## P5.T9.2 Playbook Updates

Update response plans based on lessons learned.

<a id="p5-t9-3"></a>

## P5.T9.3 Model Retraining

Retrain to mitigate drift; incorporate human feedback.

<a id="p5-t9-4"></a>

## P5.T9.4 Patch Management

Monitor and apply patches for AI frameworks and libraries.

<a id="p5-t9-5"></a>

## P5.T9.5 Dependency Remediation

Update dependencies; prioritize based on risk.

<a id="p5-t9-6"></a>

## P5.T9.6 Policy Evolution

Annual review of governance policies; align with regulations.

<a id="p5-t9-7"></a>

## P5.T9.7 Emerging Threats

Procedures for zero-day threats; threat hunting.

<a id="p5-t9-8"></a>

## P5.T9.8 Capability Enhancements

Invest in new tools; pilot security technology.

<a id="p5-t9-9"></a>

## P5.T9.9 Performance Optimization

Optimize latency and cost; implement caching.

<a id="p5-t9-10"></a>

## P5.T9.10 Lessons Learned

Conduct post-incident reviews; share findings.

<a id="p5-t10-1"></a>

## P5.T10.1 Operator Training

Technical skills; security practices; incident response.

### C50 inherited requirement detail

A control can be technically correct and routinely bypassed because it is unusable. Extend adoption and education with tested implementation paths. Simpler paths must retain consequence-based minimums.

**Source and research** Wave 04 Holds second-order effects and quickstart critique; Wave 02 small-organization profile

[Research decision](../research/074_v35_c50.md)

- **P5.T10.1.R01** (Requirement) Publish role-specific build, fix, defend and assess paths with applicable prerequisites.
- **P5.T10.1.R02** (Requirement) Provide a low-consequence local fixture before recommending customer-facing or production automation.
- **P5.T10.1.R03** (Requirement) Measure false blocks, completion, time to diagnose and recovery alongside safety outcomes.
- **P5.T10.1.R04** (Requirement) Offer accessible escalation and recovery instructions and declare unsupported environments.

**Acceptance and failure analysis** Have a new adopter complete a synthetic build/fix/defend exercise. Capture errors and burden, and verify that simplification does not remove applicable critical safeguards.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="p5-t10-2"></a>

## P5.T10.2 Security Awareness

Training for all users on prompt injection and privacy risks.

<a id="p5-t10-3"></a>

## P5.T10.3 Safe Prompting

Educate on safe engineering practices and jailbreak prevention.

<a id="p5-t10-4"></a>

## P5.T10.4 Incident Drills

Conduct regular simulations and tabletops.

<a id="p5-t10-5"></a>

## P5.T10.5 Policy Communication

Communicate policies effectively to stakeholders.

<a id="p5-t10-6"></a>

## P5.T10.6 Industry Sharing

Participate in forums; share best practices.

<a id="p5-t10-7"></a>

## P5.T10.7 Internal Documentation

Maintain Wikis, FAQs, and Runbooks.

<a id="p5-t10-8"></a>

## P5.T10.8 Vendor Training

Require security training for third-party vendors.

<a id="p5-t10-9"></a>

## P5.T10.9 Role-Based Training

Tailored content for Developers, Operations, and Compliance.

<a id="p5-t10-10"></a>

## P5.T10.10 Culture

Foster responsibility; reward secure practices.

<a id="p5-t1-1_adv"></a>

## P5.T1.1_ADV Swarm Evolution

Test new agent capabilities in isolation; improve consensus logic based on data.

<a id="p5-t1-2_adv"></a>

## P5.T1.2_ADV Supply Chain Evolution

Track OpenSSF Model Signing specification updates; align with ISO/NIST supply chain rules.

<a id="p5-t1-3_adv"></a>

## P5.T1.3_ADV NHI Posture

Optimize provisioning and rotation; integrate NHI-specific threat feeds.

<a id="p5-t1-4_adv"></a>

## P5.T1.4_ADV Memory Defense Evolution

Update poison detection algorithms based on new research; architecture reviews for memory attacks.

<a id="p5-t2-1_adv"></a>

## P5.T2.1_ADV Swarm Training

Swarm Manager certifications; red team simulations targeting multi-agent systems.

<a id="p5-t2-2_adv"></a>

## P5.T2.2_ADV NHI Awareness

Credential theft and privilege escalation training; secret hygiene education.

<a id="p5-t2-3_adv"></a>

## P5.T2.3_ADV Supply Chain Culture

Model signing training; SBOM generation and validation education.

<a id="p5-t2-4_adv"></a>

## P5.T2.4_ADV Memory Awareness

RAG security best practices; poisoning awareness and detection training.

<a id="e5-1"></a>

## E5.1 Continuous Adversarial Evaluation Cadence

Mandatory evaluation gates triggered by model updates, prompt changes, tool additions, and quarterly cadence - tests the current system, not the system as deployed months ago.

### C16 inherited requirement detail

C04 owns the assurance rule. P4 and P5 own live observation and validation. Parallel core controls would blur independent evidence and model-justification signals.

**Source and research** Evidence waves 01-06; C16 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/040_v35_c16.md)

- **E5.1.R01** (Requirement) Protect evaluation inputs, test selection, graders and live monitors from agent modification.
- **E5.1.R02** (Requirement) Evaluate actions and effects independently of model justification; record shared-source and evaluation-awareness limitations.

**Acceptance and failure analysis** Evaluation integrity and protected monitoring. Separate grader custody, test recognition, contaminated results and false completion.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C32 inherited requirement detail

Preserve the hypotheses and contrary evidence. Keep cognitive scoring out of normative enforcement until validity, privacy and practical benefit are demonstrated.

**Source and research** Evidence waves 01-06; C32 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/056_v35_c32.md)

- **E5.1.R03** (Research requirement) Document the validity, limitations, affected population and privacy of candidate cognitive and evaluator measurements before using them as gates.
- **E5.1.R04** (Research requirement) Preserve contrary evidence and speculative status; threshold adoption requires a scoped validation decision.

**Acceptance and failure analysis** Research notes on capability reserve, evaluation-aware behavior, and comparative validation. Define disconfirming outcomes and repeatability before proposing new requirements.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="e5-2"></a>

## E5.2 Capability Emergence Review Process

Structured governance for emergent agent capabilities: Tier 1 document, Tier 2 security review, Tier 3 board approval, Tier 4 suspend pending investigation.

### C22 inherited requirement detail

Use existing privacy, provenance and evaluation objectives. Profile the extra duties when training or fine-tuning applies. Broad requirements burden deployments that never train.

**Source and research** Evidence waves 01-06; C22 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/046_v35_c22.md)

- **E5.2.R01** (Requirement) Record authorization and provenance for training, fine-tuning and derived copies, with applicable privacy and extraction evaluations.
- **E5.2.R02** (Requirement) Reassess changes in model, prompt, data, memory policy, tools and effective capability before consequential use.

**Acceptance and failure analysis** Model and data lifecycle. Document authorized purpose, derived copies, risk evaluations and change triggers.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="e5-3"></a>

## E5.3 Evaluation-Safe Pattern Library

Validated reference implementations for all AI SAFE2 controls with platform-specific variants for Bedrock, Azure AI, LangGraph, AutoGen, n8n, and CrewAI.

<a id="e5-4"></a>

## E5.4 Red-Team Artifact Repository

Structured schema for all red-team findings; required deliverable from every exercise; integrated into E5.1 evaluation cadence for continuous reuse.

<a id="s1-8"></a>

## S1.8 Pre-Trust Initialization Boundary

Before trust is established, prevent project or externally supplied hooks, helpers, plugins, package scripts, credential reads and network callbacks from executing.

### C02 inherited requirement detail

The boundary precedes normal task authorization. A generic sandbox control can miss startup behavior. A distinct control introduces a separate platform verification burden.

**Source and research** Evidence waves 01-06; C02 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/026_v35_c02.md)

- **S1.8.R01** (Requirement) Before trust is established, prevent project or externally supplied hooks, helpers, plugins, package scripts, credential reads and network callbacks from executing.
- **S1.8.R02** (Requirement) Separate preview and discovery from execution and credential access; inventory all enabled startup paths.
- **S1.8.R03** (Requirement) Exercise hostile synthetic projects and preserve process, file and network observations together with a valid trusted-project control.

**Acceptance and failure analysis** Pre-trust execution in harnesses. Verify synthetic untrusted project opening has zero prohibited effects and trusted opening still works.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="f3-6"></a>

## F3.6 Aggregate Consumable-Authority Ceiling

Reserve shared task and descendant resource budgets before admitting concurrent work; account for outstanding and settled consumption.

### C05 inherited requirement detail

F3.2 controls depth, F3.5 contains cascades, MCP-8 is profile-scoped and APAY handles payments. Shared reservations across parallel descendants are separately testable. Strong consistency can affect availability.

**Source and research** Evidence waves 01-06; C05 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/029_v35_c05.md)

- **F3.6.R01** (Requirement) Reserve shared task and descendant resource budgets before admitting concurrent work; account for outstanding and settled consumption.
- **F3.6.R02** (Requirement) Declare units, accountable owner, concurrency, retries, expiry and treatment of delayed or unknown consumption.
- **F3.6.R03** (Requirement) Reject admission beyond the aggregate envelope, reconcile cancellation and settlement idempotently, and define safe handling of partially committed effects.

**Acceptance and failure analysis** Aggregate authority and settlement. Compare concurrency, tokens, commitments, retry and delayed usage. Allocate F3.6 only after catalog overlap review.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C47 inherited requirement detail

Spend alone omits material compute, energy, water and infrastructure constraints. Add applicability-based measurement and limits. Precise measurement may be unavailable for hosted services.

**Source and research** Wave 02 environmental/resource impacts; Wave 04 generalized consumable authority

[Research decision](../research/071_v35_c47.md)

- **F3.6.R04** (Requirement) Identify material infrastructure and environmental constraints for the deployment.
- **F3.6.R05** (Requirement) Record measured, provider-reported, estimated and unknown resource use separately.
- **F3.6.R06** (Requirement) Apply justified limits or procurement restrictions and recheck after scaling or model changes.

**Acceptance and failure analysis** Compare measured use and estimates under a synthetic scaling scenario. Avoid turning uncertain estimates into exact environmental benefits.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="f3-7"></a>

## F3.7 Environment Binding and Assertion

Bind action authority to a verified environment, tenant and resource identity.

### C34 inherited requirement detail

Isolation alone does not establish which environment an authorized action targets. A distinct effect gate makes production/development assertions independently testable. Environment identity management and emergency procedures add operational cost.

**Source and research** Wave 04 Holds, Environment Binding and Assertion; Wave 02 purpose separation

[Research decision](../research/058_v35_c34.md)

- **F3.7.R01** (Requirement) Bind action authority to a verified environment, tenant and resource identity.
- **F3.7.R02** (Requirement) Require an independently issued environment assertion for destructive or material operations.
- **F3.7.R03** (Requirement) Refuse a mismatched, expired or unknown environment assertion and prevent agent self-issuance.
- **F3.7.R04** (Requirement) Revalidate after a route, account, region, resource alias or environment change.

**Acceptance and failure analysis** Run synthetic development/production twins and verify that changed endpoint or account cannot redirect an approval. Validate the cited incidents individually before attributing their causes.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="a2-7"></a>

## A2.7 Idempotency and Side-Effect Ledger

Bind each idempotency key to task, operation, destination and canonical action parameters.

### C18 inherited requirement detail

Idempotency, conflict resolution, compensation and unknown outcomes reuse recovery obligations. APAY retains settlement-specific details.

**Source and research** Evidence waves 01-06; C18 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/042_v35_c18.md)

- **A2.7.R01** (Requirement) Define transaction boundaries, shared-state ownership, locks, conflict handling, retries and compensation.
- **A2.7.R02** (Requirement) Preserve unknown outcomes until an authoritative state observation or accountable reconciliation resolves them.

**Acceptance and failure analysis** Retries, partial effects and concurrent state. Measure duplicates, conflicts and observed recovery with a synthetic destination.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C35 inherited requirement detail

C18 compressed ledger semantics into general transaction safety. Reservation, commitment and unknown outcomes warrant an explicit reusable requirement. P2 records evidence; the P3 mechanism prevents duplicate effects. Central state adds collision and availability risks.

**Source and research** Wave 04 Holds, Idempotency and Side-Effect Ledger; Wave 02 ASG-13 and transactions

[Research decision](../research/059_v35_c35.md)

- **A2.7.R03** (Requirement) Bind each idempotency key to task, operation, destination and canonical action parameters.
- **A2.7.R04** (Requirement) Reserve and commit the operation atomically where supported; reject key reuse for a different action.
- **A2.7.R05** (Requirement) Reconcile ambiguous results against destination state before retrying an irreversible effect.
- **A2.7.R06** (Requirement) Define retention, collision handling, timeout, partial completion and compensation semantics.
- **A2.7.R07** (Requirement) Return the recorded result for a completed identical request without executing it again.

**Acceptance and failure analysis** Exercise concurrent duplicate requests, key collision, timeout after commit and ledger outage. Document external services where exact duplicate suppression cannot be established.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="a2-8"></a>

## A2.8 Verified Outcome Contract

Declare the external postcondition and its authoritative observation method.

### C36 inherited requirement detail

C04 concerns evidence independence across claims. This objective defines completion itself. Existing receipt tooling does not make an external business outcome verified. Additional observations can add latency and expose sensitive state.

**Source and research** Wave 04 Holds, Post-Condition Verification; Wave 02 P2-01; merged CI receipt boundary

[Research decision](../research/060_v35_c36.md)

- **A2.8.R01** (Requirement) Declare the external postcondition and its authoritative observation method.
- **A2.8.R02** (Requirement) Distinguish attempted, accepted, committed, independently verified, failed and unknown outcomes.
- **A2.8.R03** (Requirement) Bind the observation to the action, target, revision and observation time.
- **A2.8.R04** (Requirement) Prevent a tool success response or agent completion message from alone satisfying the postcondition.
- **A2.8.R05** (Requirement) Scope verification frequency and retention to consequence and preserve unknown coverage.

**Acceptance and failure analysis** Return HTTP success without the intended state change, then mutate the wrong target. Both remain incomplete or failed. Include legitimate success and an unavailable observer.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="e5-5"></a>

## E5.5 Declared Success Criteria Gate

Declare intended benefit, observable success, prohibited effects and accepted uncertainty before consequential operation.

### C37 inherited requirement detail

Evaluation cadence cannot compensate for a missing task objective. This gate applies at design and acceptance time, while C36 applies after execution. Exploratory and qualitative work need explicit human review criteria instead of fabricated machine precision.

**Source and research** Wave 04 Holds, Declared Success Criteria Gate; Wave 02 G-01 and P5 requirements

[Research decision](../research/061_v35_c37.md)

- **E5.5.R01** (Requirement) Declare intended benefit, observable success, prohibited effects and accepted uncertainty before consequential operation.
- **E5.5.R02** (Requirement) Use executable assertions where feasible and identify the responsible human rubric when judgment remains necessary.
- **E5.5.R03** (Requirement) Bind criteria to the workflow version and prevent the acting agent from relaxing them after observing its result.
- **E5.5.R04** (Requirement) Keep task completion, safety, utility and cost as separate outcomes.

**Acceptance and failure analysis** Demonstrate that a workflow with no criteria cannot claim validated completion. Test correct assistance, safe refusal, false blocking and an approved exploratory task. Recheck the source of the supplied 41% figure.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="a2-9"></a>

## A2.9 Evidence-Based Failure Attribution

Record failures by environment, build, transport, harness, application, postprocessing, publication and applicable runtime boundary.

### C38 inherited requirement detail

Observed failure location and causal root cause are different claims. Existing CI phase classification provides a bounded implementation to generalize. A distinct requirement makes repair guidance testable. Evidence collection can be incomplete and causality may remain unresolved.

**Source and research** Wave 04 Holds, Failure Location; Developer Workflow CI execution receipt; Wave 02 outcome evidence

[Research decision](../research/062_v35_c38.md)

- **A2.9.R01** (Requirement) Record failures by environment, build, transport, harness, application, postprocessing, publication and applicable runtime boundary.
- **A2.9.R02** (Requirement) Attach observations, competing explanations and unavailable evidence to each proposed failure location.
- **A2.9.R03** (Requirement) Keep ranked hypotheses distinct from verified causes and explicit unknown states.
- **A2.9.R04** (Requirement) Link each accepted diagnosis to a repair and a repeat of the relevant failing case.

**Acceptance and failure analysis** A passing application test followed by a broken wrapper must retain both observations. Compare diagnoses with an independently labeled synthetic fault set before claiming superiority over published work.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="cp-1"></a>

## CP.1 Agent Failure Mode Taxonomy

Classify observed agent failures by actor/origin, input surface, authority, effect, enforcement point and recovery. Use request, handle_scoped, durable and swarm_shared persistence with explicit uncertainty.

<a id="cp-2"></a>

## CP.2 Adversarial ML Threat Model Integration

Mandatory governance artifact for ACT-2+ deployments mapping every threat with temporal_profile=(immediate|delayed_days|delayed_weeks|chronic) to capture time-shifted attacks.

<a id="cp-3"></a>

## CP.3 ACT Capability Tiers 1-4

Four-tier agent classification system (Assisted/Supervised/Autonomous/Orchestrator) with mandatory control requirements that scale with autonomy level. ACT-3/ACT-4 require HEAR designation.

### C07 inherited requirement detail

ACT tiers already determine capability. Add an independent consequence classification so low-autonomy systems with high impact get appropriate review. A separate core control becomes warranted if rights governance needs its own owner and lifecycle.

**Source and research** Evidence waves 01-06; C07 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/031_v35_c07.md)

- **CP.3.R01** (Requirement) Classify consequence, reversibility, data sensitivity, affected populations and applicability separately from autonomy.
- **CP.3.R02** (Requirement) Require proportionate review for high-impact decisions even at low ACT tiers.

**Acceptance and failure analysis** Capability versus consequence. Compare high-impact low-autonomy and low-impact high-autonomy cases, including vulnerable and nonparticipating people.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C41 inherited requirement detail

Security and valid authority can coexist with invalid or unfair decisions. Existing impact and oversight homes need explicit statistical and accessibility requirements. Context-specific metrics and conflicting objectives require recorded choices.

**Source and research** Wave 02 governance/fairness; Wave 06 rubric C13 and source crosswalk

[Research decision](../research/065_v35_c41.md)

- **CP.3.R03** (Requirement) Declare decision validity, affected populations, accessibility needs and task-specific fairness objectives.
- **CP.3.R04** (Requirement) Record sample size, power rationale where applicable, effect sizes, uncertainty and subgroup limitations.
- **CP.3.R05** (Requirement) Distinguish nonsignificant results from established absence of harmful disparities.
- **CP.3.R06** (Requirement) Define mitigation that can change the decision, use restrictions or deployment and monitor its outcome.

**Acceptance and failure analysis** Evaluate authorized decisions that are systematically wrong or inaccessible. A mitigation must change relevant outcomes. Keep legal applicability and CSI-defined numerical thresholds attributed separately.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="cp-4"></a>

## CP.4 Agentic Control Plane Governance

Defines the Agentic Control Plane - agent identity, dynamic permission enforcement, orchestration boundaries, runtime behavioral trust - as a board-visible governance concept. Protocol-layer meshes (A2A, MCP, ACP) must be evaluated against CP.3-CP.7.

### C08 inherited requirement detail

Trusting content and granting authority are separate decisions within existing policy and isolation boundaries. One parent avoids divergent grants across surfaces.

**Source and research** Evidence waves 01-06; C08 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/032_v35_c08.md)

- **CP.4.R01** (Requirement) Separate information content from policy and action authority; untrusted content shall not add, widen or remove grants.
- **CP.4.R02** (Requirement) Treat source signatures as provenance and independently decide suitability, authorization and corroboration.

**Acceptance and failure analysis** Information, provenance and authority. Verify that untrusted data can inform reasoning without changing grants and that shared-source claims cannot establish independence.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C44 inherited requirement detail

An exception can permanently defeat all otherwise correct controls. Existing ownership is appropriate if authority, expiry and monitoring become mandatory. Tight emergency rules can impede urgent recovery.

**Source and research** Wave 02 emergency powers, governance-agent authority and policy integrity

[Research decision](../research/068_v35_c44.md)

- **CP.4.R03** (Requirement) Bind exceptions to a named authority, scope, reason, expiry and compensating measures.
- **CP.4.R04** (Requirement) Prevent an acting or governance agent from approving its own exceptions or extending their lifetime.
- **CP.4.R05** (Requirement) Log use, require post-event review and verify restoration of normal policy.
- **CP.4.R06** (Requirement) Define a tested emergency path for unavailable approvers with limited consequences.

**Acceptance and failure analysis** Exercise expired exceptions, approver outage and an agent requesting wider rights. Verify revocation and restoration after the emergency.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="cp-5"></a>

## CP.5 Platform-Specific Agent Security Profiles

Per-platform companion documents (Bedrock, Azure AI Foundry, n8n, LangGraph, AutoGen, CrewAI) mapping SAFE2 controls to platform CVEs, implementation guidance, and monitoring telemetry. Protocol-layer meshes assessed as supply chain components.

### C25 inherited requirement detail

C02 owns the universal pre-trust rule. Coding and IDE profiles need startup, workspace, skill and permission-change checks. A profile improves specificity at the cost of version tracking.

**Source and research** Evidence waves 01-06; C25 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/049_v35_c25.md)

- **CP.5.R01** (Requirement) For coding harnesses, enumerate and gate project startup, hooks, skills, helpers, credentials and configured subprocesses.
- **CP.5.R02** (Requirement) Bind changed workspace, skill and endpoint permissions to a reviewed trust decision.

**Acceptance and failure analysis** Harness startup and skill composition. Document which launch and update paths are actually covered.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C26 inherited requirement detail

Gateways need policy/admin separation, upstream attribution, verified fallback and egress boundaries. Reuse C01, C03, C16 and C17. A separate core would duplicate policy authority.

**Source and research** Evidence waves 01-06; C26 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/050_v35_c26.md)

- **CP.5.R03** (Requirement) For inference gateways, separate administrative policy, upstream credentials and execution authority from model responses.
- **CP.5.R04** (Requirement) Record actual routing and prevent unapproved endpoint or model substitution and permissive fallback.

**Acceptance and failure analysis** Inference routing and gateway trust. Measure actual provider attribution and enforcement across approved routes.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C27 inherited requirement detail

Evaluation and training environments need dedicated isolation, scope, stopping and evidence custody. Reuse C04 and C16. Profile-specific rules prevent transferring assumptions to ordinary deployments.

**Source and research** Evidence waves 01-06; C27 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/051_v35_c27.md)

- **CP.5.R05** (Requirement) For evaluation environments, isolate runs, shared package services, secrets, graders and external destinations.
- **CP.5.R06** (Requirement) Enforce the authorized scope and verified containment independently of tested-agent behavior.

**Acceptance and failure analysis** Evaluation infrastructure as an operating boundary. Verify scope and independent results on synthetic infrastructure.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C28 inherited requirement detail

Separate enterprise and personal purpose, account, bystander consent, browser state and offboarding. Core consent and isolation still apply.

**Source and research** Evidence waves 01-06; C28 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/052_v35_c28.md)

- **CP.5.R07** (Requirement) For personal agents, separate personal and enterprise accounts, state, purposes, consent and offboarding.
- **CP.5.R08** (Requirement) Keep bystander data and derived-state reuse within explicitly recorded scope.

**Acceptance and failure analysis** Personal-agent authority and continuity. Verify account separation and derived-data revocation across session changes.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C29 inherited requirement detail

Preserve transaction intent, merchant conflicts, cumulative limits and settlement truth. Add a distinct finance profile only for verified institutional duties beyond APAY. Quorum should depend on consequence and applicable policy.

**Source and research** Evidence waves 01-06; C29 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/053_v35_c29.md)

- **CP.5.R09** (Requirement) For commerce, bind buyer, merchant, amount, terms, destination, recurring commitments and settlement authority.
- **CP.5.R10** (Requirement) Disclose configured incentives and verify settlement and refund outcomes through independent evidence.

**Acceptance and failure analysis** Agent commerce, conflicts and obligations. Compare purchase, recurring commitment, refund and settlement cases.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C30 inherited requirement detail

Existing MCP-19, MCP-18 and related controls offer a home for discovery, audience, identity, catalog changes and fallback. New IDs require an uncovered objective after exact mapping.

**Source and research** Evidence waves 01-06; C30 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/054_v35_c30.md)

- **CP.5.R11** (Requirement) Apply the v3.5 MCP child requirements and preserve protocol-independent governance units.
- **CP.5.R12** (Requirement) Validate capability, resource, principal, destination and current-state bindings through the actual deployment paths.

**Acceptance and failure analysis** MCP actor/origin, surface and enforcement. Compare repeated incidents across dates and produce version-bounded conformance evidence.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C31 inherited requirement detail

A local controller, safety envelope and safe degraded state differ materially from ordinary digital tools. Generalize final-effect authorization while keeping physical assurance domain-specific.

**Source and research** Evidence waves 01-06; C31 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/055_v35_c31.md)

- **CP.5.R13** (Requirement) For physical effects, enforce a domain-specific safety envelope and a locally available safe degraded state.
- **CP.5.R14** (Requirement) Exercise connectivity loss, cloud outage and agent termination without introducing unsafe controller behavior.

**Acceptance and failure analysis** Physical action and degraded operation. Use synthetic device states and measure recovery and human intervention.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C40 inherited requirement detail

Browser interfaces and native apps have distinct observation and action semantics. A browser-only profile loses native computer-use evidence. Shared final-effect controls remain inherited. Image and accessibility observations can be incomplete.

**Source and research** Wave 04 Holds, CP.5.CUA; Wave 01 Google Home specificity

[Research decision](../research/064_v35_c40.md)

- **CP.5.R15** (Requirement) Record target application, account, document or page identity and relevant state before a material action.
- **CP.5.R16** (Requirement) Require an observation fresh enough to identify the intended control and handle asynchronous state changes.
- **CP.5.R17** (Requirement) Recheck the target after focus, navigation, layout, modal or account changes.
- **CP.5.R18** (Requirement) Verify the resulting application or business state independently of the click or screenshot.
- **CP.5.R19** (Requirement) Declare unsupported surfaces and evidence limitations; keep native-app and browser fixtures distinct.

**Acceptance and failure analysis** Exercise stale screenshots, delayed page state, changed window focus, modal interception and a click that leaves the postcondition unmet. Preserve the source DOM-settle proposal as browser-specific treatment.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="cp-6"></a>

## CP.6 AI Incident Feedback Loop Integration

Quarterly AIID agentic incident reviews plus 30-day Incident-Informed Control Review (IICR) triggered by new relevant AIID incidents. Internal Agentic Incident Registry required.

### C20 inherited requirement detail

Retain feedback-loop ownership. Add applicable clock, role, evidence hold and disposition, with source-pinned obligation profiles. Centralizing legal conclusions in core would reduce portability.

**Source and research** Evidence waves 01-06; C20 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/044_v35_c20.md)

- **CP.6.R01** (Requirement) Route incident reporting, evidence holds, applicable clocks and recipients using a source-pinned obligation record.
- **CP.6.R02** (Requirement) Convert material incidents into owned regression cases or record a justified disposition and revisit trigger.

**Acceptance and failure analysis** From incident to owned regression. Compare discovery and disclosure dates, overlapping duties, closure evidence and reasons for exclusions.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C49 inherited requirement detail

The plan emphasized mechanisms but did not require an operational intelligence product. Incident learning needs actor behavior, prerequisites and detection opportunities. Public attribution and prevalence can remain uncertain.

**Source and research** Wave 01 actors and operational developments; Wave 03 timelines and indicators

[Research decision](../research/073_v35_c49.md)

- **CP.6.R03** (Requirement) Record observed actions, entry points, prerequisites, effects and sources independently from actor attribution.
- **CP.6.R04** (Requirement) Distinguish advisory, laboratory demonstration, observed exploitation and sustained operational activity.
- **CP.6.R05** (Requirement) Link relevant techniques to detection, prevention, containment and regression cases with exact deployment scope.
- **CP.6.R06** (Requirement) Preserve event, discovery, disclosure and fix dates, revisions, contradictions and confidence.
- **CP.6.R07** (Requirement) Use evidence-driven update triggers and publish changes in source confidence without manufacturing population incident rates.

**Acceptance and failure analysis** Turn one source-backed incident into a linked control/detection/test record and retain both the original disclosure and later correction. Forecasts carry falsifiers and remain distinct from recorded events.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="cp-7"></a>

## CP.7 Deception & Active Defense Layer

AI-specific active defense: canary documents in RAG corpora, honeypot tool endpoints, fake credential traps in agent memory. First deception-class control in any AI governance framework.

<a id="cp-8"></a>

## CP.8 Catastrophic Risk Threshold Controls

Behavioral indicators triggering emergency suspension regardless of business continuity impact: unauthorized compute acquisition, communication outside approved list, weaponizable capability. CRT documentation required for ACT-3/ACT-4 deployment approval.

### C43 inherited requirement detail

Per-deployment fallback and independent agent identities miss shared providers, models, policies and evaluators. A portfolio assessment extends existing continuity and threshold ownership. Independence can cost money and introduce operational complexity.

**Source and research** Wave 02 divergent governance ideas; swarm common-mode evidence

[Research decision](../research/067_v35_c43.md)

- **CP.8.R01** (Requirement) Inventory shared model, provider, route, identity, policy, dataset and evaluator dependencies across deployments.
- **CP.8.R02** (Requirement) Assess correlated loss or defect scenarios and bound cumulative exposure.
- **CP.8.R03** (Requirement) Exercise an approved alternative and document dependencies shared with the primary path.
- **CP.8.R04** (Requirement) Review concentration after material acquisitions, migrations and new deployments.

**Acceptance and failure analysis** Disable a shared policy or provider in a synthetic multi-deployment estate and measure which fallback paths are actually independent.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="cp-9"></a>

## CP.9 Agent Replication Governance (ARG)

First governance standard for agent replication. Requires: replication authority in deployment manifests enforced at gateway; ephemeral credentials with scope narrowing per delegation hop; cryptographic lineage tokens; ACT-3 max 2 hops, ACT-4 max 3 hops; 500ms full delegation-tree severance on kill signal.

### C09 inherited requirement detail

CP.9 already owns descendant lineage. Add resource-side enforcement of bound purpose, scope, expiry and root task. Independent core IDs would duplicate the lifecycle.

**Source and research** Evidence waves 01-06; C09 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/033_v35_c09.md)

- **CP.9.R01** (Requirement) Bind each descendant to the root task, verified principal, purpose, permitted resources, expiry and equal or narrower authority.
- **CP.9.R02** (Requirement) Verify the delegation at the final resource; deny fallback from missing identity to shared operator authority.

**Acceptance and failure analysis** End-to-end delegated identity. Verify that a valid child identity cannot widen scope or survive expiry and revocation.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="cp-10"></a>

## CP.10 HEAR Doctrine (Human Ethical Agent of Record)

Named individual with cryptographic signing key, real-time interrupt capability, and unilateral kill-switch authority for all ACT-3/ACT-4 deployments. Class-H actions require HEAR signature before execution. Fail-closed: no automatic approval path.

### C10 inherited requirement detail

Retain HEAR authority and existing recovery ownership. Require descendant and queued-work observations plus recovery of committed effects. A combined implementation can carry a coordination cost.

**Source and research** Evidence waves 01-06; C10 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/034_v35_c10.md)

- **CP.10.R01** (Requirement) Provide an authenticated stop and revocation path outside the acting agent and independent of swarm voting.
- **CP.10.R02** (Requirement) Enumerate descendants, queued jobs, sessions and in-flight effects; verify cessation or isolate unresolved work and record residual effects.

**Acceptance and failure analysis** Stop, revocation convergence and residual effects. Compare delay, partitions, restarts and externally committed work.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C24 inherited requirement detail

Keep the machine/human division and add comprehension, time, scope and practical intervention. A new CP.11 would duplicate existing ownership.

**Source and research** Evidence waves 01-06; C24 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/048_v35_c24.md)

- **CP.10.R03** (Requirement) Test whether the reviewer receives material evidence, understands the proposed scope and can intervene under realistic time and accessibility constraints.
- **CP.10.R04** (Requirement) Measure justified acceptance and rejection and retained capability separately from threat severity and override frequency.

**Acceptance and failure analysis** Paired CSF and AI SAFE2 evaluation. Compare formal approval with justified reliance, evidence received and retained unaided capability.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="cp-11"></a>

## CP.11 Trust Lifecycle Governance

Establish separate trust decisions at discovery, installation, initial approval, material change, task admission, action commitment and revocation.

### C01 inherited requirement detail

Discovery, installation, change, use and revocation span CP.4 and CP.5. A shared objective prevents each profile inventing its own state model. It adds ownership and migration cost.

**Source and research** Evidence waves 01-06; C01 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/025_v35_c01.md)

- **CP.11.R01** (Requirement) Establish separate trust decisions at discovery, installation, initial approval, material change, task admission, action commitment and revocation.
- **CP.11.R02** (Requirement) Bind each decision to the component version, owner, purpose, permitted effects and expiry; invalidate affected grants after a material change.
- **CP.11.R03** (Requirement) Record the evidence and outcome of each gate and verify that retirement, offboarding and restore cannot reactivate stale authority.

**Acceptance and failure analysis** Trust between discovery and retirement. Compare install, update, dormant schedules and restoration. Show which decision expires at each transition.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="cp-12"></a>

## CP.12 Final-Effect Authorization

Immediately before committing a consequential effect, an enforcement point outside the acting model shall validate principal, delegation, action, resource, environment, recipient, purpose, time, limits and required approval.

### C03 inherited requirement detail

The action can become inadmissible after approval even with correct identity and tool permissions. CP.4 remains the supporting control plane. A standalone requirement costs adapter and commit-boundary work.

**Source and research** Evidence waves 01-06; C03 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/027_v35_c03.md)

- **CP.12.R01** (Requirement) Immediately before committing a consequential effect, an enforcement point outside the acting model shall validate principal, delegation, action, resource, environment, recipient, purpose, time, limits and required approval.
- **CP.12.R02** (Requirement) Bind approval to canonical action parameters and current policy/state versions; a changed material condition requires a new decision.
- **CP.12.R03** (Requirement) Refuse missing, expired, conflicting or unverified mandatory conditions and protect the gate and credentials from the governed agent.
- **CP.12.R04** (Requirement) Define atomic check/commit or destination-enforced version checks, replay resistance and the behavior for an unavailable authority service.

**Acceptance and failure analysis** Authority at commitment. Compare EFA, FlowSignal and AI SAFE2 using changed state, changed target, and an independently observed effect.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C11 inherited requirement detail

A separate boundary is useful for publication, communication, account creation and external commitments. It reuses final-effect authorization. A public-world control family would duplicate authority requirements.

**Source and research** Evidence waves 01-06; C11 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/035_v35_c11.md)

- **CP.12.R05** (Requirement) Require explicit scoped authority for account creation, publication, external communication, submission and financial or other commitments.
- **CP.12.R06** (Requirement) Record affected parties, intervention, takedown and recovery paths for public-facing effects.

**Acceptance and failure analysis** Agents acting beyond the operator boundary. Differentiate affected-party exposure, capability grants, containment and remedy.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="cp-13"></a>

## CP.13 Control Evidence Independence

Maintain authorization, observed action and external effect evidence through a collection boundary the acting agent cannot rewrite.

### C04 inherited requirement detail

Logging, receipt generation, grader custody and effect verification have different trust dependencies. Shared rules reduce false assurance. Independence costs integration and may constrain legacy deployments.

**Source and research** Evidence waves 01-06; C04 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/028_v35_c04.md)

- **CP.13.R01** (Requirement) Maintain authorization, observed action and external effect evidence through a collection boundary the acting agent cannot rewrite.
- **CP.13.R02** (Requirement) Record evidence provenance, collector scope, independence, freshness, uncertainty and unavailable observations without claiming hidden reasoning access.
- **CP.13.R03** (Requirement) Protect the evidence store and evaluator configuration; allow external incident and affected-party observations to challenge the recorded outcome.

**Acceptance and failure analysis** Independent evidence and false assurance. Demonstrate disagreement among a receipt, reported completion and observed resource state.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C48 inherited requirement detail

Independent custody alone cannot establish evaluator competence or representative tests. The evidence contract needs reviewer capability, conflicts and dispute handling. Independent review adds cost and may remain unavailable.

**Source and research** Wave 02 assurer independence; Wave 06 rubric disagreement process

[Research decision](../research/072_v35_c48.md)

- **CP.13.R04** (Requirement) Record reviewer competence, tool scope, financial or organizational conflicts and access limits.
- **CP.13.R05** (Requirement) Protect test selection, grader configuration and evidence custody from the evaluated agent.
- **CP.13.R06** (Requirement) Preserve reviewer disagreement and its adjudication with traceable reasons.
- **CP.13.R07** (Requirement) Retest after material changes to a benchmark, evaluator or assurance provider.

**Acceptance and failure analysis** Use a flawed grader, conflicted reviewer and contaminated test set. Verify that their verdict cannot silently become independent assurance.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="cp-14"></a>

## CP.14 Organizational AI Management Governance

Define organizational AI scope, leadership responsibility, resources, applicable obligations and statement of applicability.

### C06 inherited requirement detail

CP.4 owns the agent control plane. Leadership, management review, independent audit and corrective action have an organizational owner. Risks duplicating management-system standards if scope is loose.

**Source and research** Evidence waves 01-06; C06 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/030_v35_c06.md)

- **CP.14.R01** (Requirement) Define organizational AI scope, leadership responsibility, resources, applicable obligations and statement of applicability.
- **CP.14.R02** (Requirement) Maintain independently reviewable risk, impact, exception, audit and corrective-action records with named owners.
- **CP.14.R03** (Requirement) Conduct management review, address findings and preserve the reason, evidence and approval for material deployment decisions.

**Acceptance and failure analysis** Organizational AIMS and accountability. Pin applicable external clauses and prove a reviewer can reconstruct scope, decisions, exceptions and corrective actions.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C42 inherited requirement detail

Purpose classification does not compare alternatives. A documented suitability decision keeps the framework useful for ordinary organizations. Assessment effort should be proportional to consequence.

**Source and research** Wave 02 divergent governance ideas; expanded external inventory

[Research decision](../research/066_v35_c42.md)

- **CP.14.R04** (Requirement) Compare AI use with a simpler deterministic or human process where consequences warrant the decision.
- **CP.14.R05** (Requirement) Record expected benefit, material uncertainty, residual harms and conditions for withdrawing AI.
- **CP.14.R06** (Requirement) Declare the deployment owner and criteria for reassessment when benefits fail to materialize.

**Acceptance and failure analysis** Compare two equally successful workflows with different exposure and maintenance costs. Preserve the rationale for selecting or rejecting automation.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C51 inherited requirement detail

The recovered 32 labels, 496 tags and 706 cells describe different levels of evidence. Preserve their lineage and deepen relationships. Mapping all controls to every framework creates false equivalence and maintenance cost.

**Source and research** All four mapping-recovery files; Wave 02 mapping schemas and retrieval contracts

[Research decision](../research/075_v35_c51.md)

- **CP.14.R07** (Requirement) Register publisher, edition, status, mapping units, role, jurisdiction, source locator and licensing constraints.
- **CP.14.R08** (Requirement) Give each relationship a stable ID, direction, type, rationale, exclusions, reviewer and review date.
- **CP.14.R09** (Requirement) Record unmapped, partially addressed, out-of-scope, disputed and unassessed dispositions explicitly.
- **CP.14.R10** (Requirement) Derive reciprocal human and machine views from the same records and invalidate stale relationships after source or control changes.
- **CP.14.R11** (Requirement) Keep historical coverage assertions attributed to their original baseline and require denominators and reviewed relationships for current coverage.

**Acceptance and failure analysis** Resolve one external requirement to exact AI SAFE2 clauses, engineering checks and evidence, then reverse the query. A missing or ambiguous external ID must produce an explicit unresolved result.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

<a id="cp-15"></a>

## CP.15 Design-Time Coordination Contract

Declare role responsibilities, allowed interactions, authoritative shared resources and accountable owner before consequential deployment.

### C14 inherited requirement detail

Several individually allowed operations can produce a prohibited root effect. Existing task policy owns combined intent. Tracking composition adds state and can limit legitimate workflows.

**Source and research** Evidence waves 01-06; C14 disposition in docs/FRAMEWORK-EVIDENCE-EXPANSION.md and docs/FRAMEWORK-UPDATE-ISSUES.md

[Research decision](../research/038_v35_c14.md)

- **CP.15.R01** (Requirement) Evaluate root-task consequences and accumulated authority across the composed workflow.
- **CP.15.R02** (Requirement) Deny a prohibited effect when decomposed into individually permitted calls or skills.

**Acceptance and failure analysis** Task-level consequences. Compare isolated permissions with authorization over a complete synthetic workflow.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

### C33 inherited requirement detail

C14 handles combined authorization and C23 handles voting. Neither requires roles, ownership or termination to be defined before a workflow starts. Independent design acceptance has its own lifecycle. Extra specification effort can slow prototyping; permit declared exploratory scope with bounded effects.

**Source and research** Wave 04 Holds, Proposed for v3.2; Wave 02 shared-resource and swarm requirements

[Research decision](../research/057_v35_c33.md)

- **CP.15.R03** (Requirement) Declare role responsibilities, allowed interactions, authoritative shared resources and accountable owner before consequential deployment.
- **CP.15.R04** (Requirement) Define completion, cancellation, termination and conflict-resolution conditions for the task graph.
- **CP.15.R05** (Requirement) Validate handoffs, cyclic dependencies, abandoned locks and competing writers before promotion.
- **CP.15.R06** (Requirement) Bind the approved coordination version to execution and revalidate changes in membership or role authority.

**Acceptance and failure analysis** Show that an allowed but contradictory set of roles is rejected before deployment; a valid graph can complete. Retain synthetic fixtures and source-specific study limitations. The supplied 79% figure needs its own primary-study denominator and applicability review.

On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.

[Framework home](../README.md) · [Machine catalog](../safe2/data/ai-safe2-controls-v3.5.json) · [Research index](../research/README.md)
