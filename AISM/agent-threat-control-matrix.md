
<div align="center">
  <img src="../assets/AISM Agent Threat Control Matrix b v2.png" alt="AISM Agent Threat Control Matrix" width="100%" />
</div>

# AISM Agent Threat and Control Matrix

**Framework:** AI SAFE² v3.0
**Organization:** Cyber Strategy Institute
**Version:** April 2026

---

## Overview

Agentic AI systems introduce a threat landscape that does not exist in traditional software environments. When an AI system can autonomously call tools, spawn sub-agents, retrieve external data, and execute multi-step workflows, the attack surface expands dramatically. Threats that are theoretical for a chatbot are operational for an autonomous agent.

This document maps the primary threat categories facing agentic AI deployments to the AISM controls that address them, with cross-references to MITRE ATLAS techniques and OWASP LLM vulnerabilities. It is organized by threat category, covering both classic AI security threats and the emerging threat landscape specific to agentic systems.

**v3.0 Update:** This matrix has been updated to reflect the AI SAFE² v3.0 Cross-Pillar Governance OS (CP.1–CP.10). Three first-in-field standards — CP.7 Deception & Active Defense, CP.9 Agent Replication Governance, and CP.10 HEAR Doctrine — are now referenced in the threat categories they directly address. A new threat category, T11 Multi-Turn Behavioral Conditioning, has been added to address the distinct attack class covered by CP controls and S1.6.

This matrix is designed for security engineers, red teams, and governance practitioners who need to understand not just what controls exist, but why they exist and what specific threats they mitigate.

---

## Threat Categories at a Glance

| # | Threat Category | Primary Attack Surface | AISM Pillars | CP Governance OS | MITRE ATLAS | OWASP LLM |
|---|---|---|---|---|---|---|
| T1 | Prompt Injection | Input boundaries, tool responses, retrieved documents | P1 Shield, P2 Ledger | CP.7 Active Defense | AML.T0051 | LLM01, LLM02 |
| T2 | Multi-Agent Exploitation | Agent-to-agent communication, orchestration trust | P1 Shield, P3 Circuit Breaker, P4 Command Center | CP.4 Control Plane, CP.9 ARG | Agent subdomain (Oct 2025) | LLM08 |
| T3 | Memory and Context Poisoning | RAG pipelines, vector stores, agent memory | P1 Shield, P2 Ledger | CP.7 RAG canaries | AML.T0000.001, AML.T0001 | LLM03 |
| T4 | Supply Chain Compromise | Model artifacts, dependencies, fine-tuning data, platform config | P1 Shield, P2 Ledger | None | AML.T0002, AML.T0005, AML.T0010 | LLM05, LLM10 |
| T5 | Non-Human Identity Abuse | Service accounts, API keys, machine identities | P1 Shield, P2 Ledger, P3 Circuit Breaker | None | None currently | LLM06 |
| T6 | Runaway Autonomy | Agent action scope, recursion, resource consumption | P3 Circuit Breaker, P4 Command Center | CP.8 Catastrophic Risk, CP.10 HEAR | AML.T0040 | LLM04, LLM08 |
| T7 | Data Exfiltration | AI output channels, tool calls, agent memory | P1 Shield, P2 Ledger | None | AML.T0057 | LLM06 |
| T8 | Model Inversion and Extraction | Inference API access, output analysis | P1 Shield, P2 Ledger | None | AML.T0005 | LLM10 |
| T9 | Adversarial Inputs | Training data, inference inputs | P1 Shield | None | AML.T0051, AML.T0057 | LLM01, LLM03 |
| T10 | Insider and Operator Threats | Governance bypasses, privilege abuse, training manipulation | P2 Ledger, P4 Command Center, P5 Learning Engine | CP.1 Failure Taxonomy | AML.T0010 | LLM09 |
| T11 | Multi-Turn Behavioral Conditioning | Multi-session context, few-shot implanting, role confusion | P1 Shield, P2 Ledger | CP.2 Threat Model | None current | LLM01 |

---

## T1: Prompt Injection

**What it is:** An adversary embeds instructions within inputs that override the agent's intended behavior. Direct injection occurs in user inputs. Indirect injection occurs when malicious instructions are embedded in documents, web pages, tool responses, or other data the agent retrieves and processes.

**Why it is especially dangerous for agents:** A traditional LLM that receives a prompt injection may produce a bad output. An autonomous agent that receives a prompt injection may execute malicious tool calls, exfiltrate data, spawn additional agents, or take actions that cannot be undone.

**Attack vectors:**
- User-provided inputs crafted to override system prompt instructions
- Malicious instructions embedded in web pages retrieved by browsing agents
- Adversarial content in documents processed by document analysis agents
- Injected instructions in tool responses from compromised external services
- Cross-agent injection where one compromised agent injects instructions into another
- Indirect injection via email content, retrieved API responses, or third-party data feeds

**AISM Controls:**

| Control | Pillar | Description |
|---|---|---|
| Adversarial prompt detection with semantic analysis | P1 Shield | Detect injection patterns across all input endpoints, not just user inputs |
| Input validation schema enforcement | P1 Shield | Reject inputs that do not conform to expected structure |
| Tool response sanitization | P1 Shield | Treat all tool responses as untrusted inputs; apply same sanitization as user inputs |
| Indirect injection surface coverage (S1.10, v3.0) | P1 Shield | Enumerate every non-prompt input channel — documents, emails, tool outputs — and apply identical sanitization rigor |
| Semantic isolation boundary enforcement (S1.3, v3.0) | P1 Shield | Architecturally separate trusted system instruction context from untrusted content processing at the inference layer |
| Agent action logging with full context | P2 Ledger | Record every agent action with the input that triggered it for post-incident analysis |
| Behavioral baseline anomaly detection | P2 Ledger | Alert when agent behavior deviates from established patterns after potential injection |
| Human approval gates for high-consequence actions | P4 Command Center | Require human review before irreversible agent actions regardless of trigger source |
| **CP.7 Deception & Active Defense Layer** | **CP Governance OS** | **Canary documents seeded in RAG corpora detect retrieval-based indirect injection; honeypot tool endpoints identify tool squatting; first deception-class control in any AI governance framework** |

**MITRE ATLAS:** AML.T0051 (Prompt Injection)
**OWASP LLM:** LLM01 (Prompt Injection), LLM02 (Insecure Output Handling)

---

## T2: Multi-Agent Exploitation

**What it is:** Attacks that target the trust relationships, communication protocols, and coordination mechanisms between agents in a multi-agent system. When agents can instruct each other, a compromised agent becomes an attack vector against all agents it can reach.

**Why it is especially dangerous for agents:** Single-agent systems have a single attack surface. Multi-agent systems have an attack surface that scales with the number of agents and inter-agent communication paths. A single compromised orchestrator agent can potentially compromise all worker agents it coordinates. When orchestrators can spawn sub-agents dynamically, the attack surface expands with every spawned delegation hop.

**Attack vectors:**
- Compromising an orchestrator agent to issue malicious instructions to worker agents
- Spoofing agent identity to inject instructions from an untrusted source
- Exploiting A2A protocol weaknesses to intercept or modify inter-agent communications
- Manipulating agent consensus mechanisms to achieve unintended decisions
- Using a low-privilege agent as a pivot point to access higher-privilege agent capabilities
- Exploiting unbounded delegation chains — spawning sub-agents with escalating permissions
- Lineage token forgery to impersonate an authorized agent in a delegation hierarchy

**AISM Controls:**

| Control | Pillar | Description |
|---|---|---|
| Agent-to-agent communication isolation in dedicated network zones | P1 Shield | Prevent unauthorized inter-agent communication paths |
| A2A protocol authentication, authorization, and encryption | P1 Shield | Every agent-to-agent message must be authenticated and authorized |
| Automated agent quarantine on behavioral anomaly detection | P1 Shield | Isolate agents showing anomalous behavior before they can propagate compromise |
| P2P agent trust scoring with reputation weighting | P1 Shield | Track agent behavior history and apply trust weights to agent communications |
| Consensus voting audit trails for multi-agent systems | P2 Ledger | Record how multi-agent consensus decisions are reached for audit and anomaly detection |
| Dynamic agent state inventory (A2.4, v3.0) | P2 Ledger | Real-time registry of every deployed agent with owner_of_record, ACT tier, tool authorizations, and control_plane_id |
| Centralized kill switch for multi-agent systems | P3 Circuit Breaker | Halt entire agent swarm from a single control point when needed |
| Multi-agent cascade containment (F3.5, v3.0) | P3 Circuit Breaker | Failed agents isolated at their boundary — downstream agents receive clean error signals rather than propagating failure |
| Consensus failure escalation to human operators | P3 Circuit Breaker | Surface unexpected consensus failures for human review immediately |
| Human approval gates for multi-agent consensus decisions | P4 Command Center | Require human authorization for consequential multi-agent decisions |
| Distributed agent health monitoring | P4 Command Center | Monitor individual agent health within multi-agent deployments |
| **CP.4 Agentic Control Plane Governance** | **CP Governance OS** | **Single authoritative policy layer over agent identity, dynamic permission enforcement, and orchestration boundaries — board-visible governance artifact; A2A, MCP, and ACP protocol meshes evaluated against CP.3-CP.7** |
| **CP.9 Agent Replication Governance (ARG)** | **CP Governance OS** | **First published governance standard for agent replication: replication authority in deployment manifests enforced at gateway; ephemeral credentials with scope narrowing per delegation hop; cryptographic lineage tokens; ACT-3 max 2 hops, ACT-4 max 3 hops; 500ms full delegation-tree severance on kill signal** |

**MITRE ATLAS:** Agent subdomain techniques (updated October 2025)
**OWASP LLM:** LLM08 (Excessive Agency)

---

## T3: Memory and Context Poisoning

**What it is:** Attacks that corrupt the information an agent retrieves, stores, or uses for context. This includes RAG (Retrieval-Augmented Generation) poisoning, vector store manipulation, long-term memory corruption, and context window injection through retrieved content.

**Why it is especially dangerous for agents:** Agents that rely on external memory and retrieval pipelines inherit the security posture of every data source they retrieve from. A poisoned vector store or corrupted RAG corpus can cause an agent to behave incorrectly across thousands of interactions without any individual input appearing adversarial.

**Attack vectors:**
- AgentPoison: injecting trigger phrases into RAG corpora that cause consistent malicious behavior when retrieved
- MINJA and PajaMAS: memory poisoning techniques that corrupt long-term agent memory stores
- Gradual poisoning: slowly introducing adversarial content into retrieval corpora to avoid detection
- Context window manipulation: crafting retrieved documents to dominate agent context and override instructions
- Thread injection: injecting malicious content into multi-turn conversation memory
- Embedding drift: systematically shifting the embedding space of a vector store toward adversarial regions

**AISM Controls:**

| Control | Pillar | Description |
|---|---|---|
| Semantic similarity analysis for gradual poison injection detection | P1 Shield | Detect slowly introduced adversarial content through baseline comparison |
| RAG poisoning detection with baseline embedding monitoring | P1 Shield | Monitor embedding space for unexpected shifts indicating corpus corruption |
| Thread injection prevention with per-agent session isolation | P1 Shield | Isolate agent context between sessions to prevent cross-session contamination |
| Memory governance boundary controls (S1.5, v3.0) | P1 Shield | Every write to persistent agent memory requires authorization, sanitization, and an append-only audit log entry — prevents unauthorized corpus modification |
| SHA-256 hashing of agent state and context for integrity verification | P1 Shield | Detect unauthorized modifications to agent context |
| Periodic RAG content audits with semantic similarity checks | P2 Ledger | Regularly audit retrieval corpora for injected adversarial content |
| RAG corpus diff tracking (A2.6, v3.0) | P2 Ledger | Hash-verified change log for the retrieval layer; automatically correlates behavioral changes to corpus changes |
| AgentPoison trigger phrase detection | P2 Ledger | Scan retrieval corpora and outputs for known trigger phrase patterns |
| Baseline embedding space monitoring | P2 Ledger | Alert on unexpected shifts in the embedding space of retrieval stores |
| Memory poisoning incident response playbook | P3 Circuit Breaker | Define specific procedures for containing and recovering from memory poisoning events |
| RAG content quarantine and restoration procedures | P3 Circuit Breaker | Procedures for isolating corrupted retrieval content and restoring clean baselines |
| Context consistency verification for agent sessions | P4 Command Center | Monitor for context anomalies that may indicate poisoning |
| **CP.7 Deception & Active Defense Layer** | **CP Governance OS** | **Canary documents seeded throughout RAG corpora detect corpus access by unauthorized agents or unusual retrieval patterns; embedding drift canaries detect gradual poisoning before behavioral change becomes detectable** |

**MITRE ATLAS:** AML.T0000.001, AML.T0001
**OWASP LLM:** LLM03 (Training Data Poisoning)

---

## T4: Supply Chain Compromise

**What it is:** Attacks that target the pipeline from model provider to production deployment. This includes model artifact tampering, malicious fine-tuning datasets, compromised dependency packages, counterfeit model distribution, and — in v3.0 — attacks on the configuration APIs of managed cloud AI platforms.

**Why it is especially dangerous for agents:** An agent built on a compromised model or dependency inherits whatever backdoors or vulnerabilities were introduced upstream. These compromises are particularly difficult to detect because the agent may appear to function normally for all standard use cases while behaving maliciously in specific triggered scenarios. Cloud AI platform configuration attacks (e.g., Bedrock UpdateGuardrail API manipulation) extend the supply chain attack surface to managed services.

**Attack vectors:**
- Model artifact tampering: replacing a legitimate model file with a maliciously modified version
- Poisoned fine-tuning data: introducing adversarial examples into fine-tuning datasets
- Dependency package compromise: injecting malicious code into model framework dependencies
- Counterfeit model distribution: distributing model files that appear legitimate but contain backdoors
- SBOM gap exploitation: using undocumented dependencies as attack vectors
- Cloud AI platform configuration attacks: manipulating Bedrock UpdateGuardrail, Azure AI Foundry configuration APIs, or other managed AI service configuration endpoints that standard CloudTrail monitoring does not capture

**AISM Controls:**

| Control | Pillar | Description |
|---|---|---|
| Cryptographic verification of imported models and datasets (SHA-256) | P1 Shield | Verify model artifact integrity at every stage from download through deployment |
| OpenSSF Model Signing (OMS) verification at model load time | P1 Shield | Cryptographically verify model provenance from source through fine-tuning to deployment |
| Provenance chain verification from base model through fine-tuning | P1 Shield | Document and verify every step in the model development lifecycle |
| Automated SBOM scanning with CVE correlation | P1 Shield | Continuously scan all model dependencies against known vulnerabilities |
| SBOM generation and maintenance for all models and applications | P2 Ledger | Maintain comprehensive inventory of all model dependencies |
| Supply chain artifact audit and provenance documentation | P2 Ledger | Record complete provenance chains for all AI artifacts |
| Model lineage provenance ledger (A2.3, v3.0) | P2 Ledger | Cryptographic chain of custody from base model through every fine-tuning stage to production; extends OpenSSF OMS |
| SBOM version control and audit trails | P2 Ledger | Track all changes to software bills of materials over time |
| Certificate expiration monitoring for model signing | P2 Ledger | Alert before model signing certificates expire to prevent enforcement gaps |
| Automated OMS signature verification in CI/CD pipelines | P2 Ledger | Enforce model signing verification at deployment time, not just at load time |
| Cloud AI platform-specific monitoring (M4.8, v3.0) | P4 Command Center | Monitor Bedrock UpdateGuardrail and UpdateDataSource APIs; Azure AI Foundry configuration changes; platform attack paths that standard CloudTrail monitoring misses |
| Platform-specific agent security profiles (CP.5, v3.0) | CP Governance OS | Per-platform companion documents for Bedrock, Azure AI Foundry, n8n, LangGraph, AutoGen, and CrewAI mapping SAFE² controls to platform CVEs and monitoring telemetry |

**MITRE ATLAS:** AML.T0002, AML.T0005 (Backdoor ML Model), AML.T0010 (Craft Adversarial Data)
**OWASP LLM:** LLM05 (Supply Chain Vulnerabilities), LLM10 (Model Theft)

---

## T5: Non-Human Identity Abuse

**What it is:** Attacks targeting the machine identities, service accounts, API keys, and automated credentials that AI systems use to access resources. As AI agents gain more autonomous capability, they require more powerful credentials, making NHI security increasingly critical.

**Why it is especially dangerous for agents:** Autonomous agents require credentials to call APIs, access databases, invoke tools, and communicate with other services. An attacker who obtains an agent's credentials can act as that agent, potentially with the same broad permissions the agent requires for its legitimate operations.

**Attack vectors:**
- Credential extraction from agent memory, logs, or environment variables
- Service account privilege escalation
- Stale credential exploitation: using credentials for decommissioned agents or services
- Lateral movement using agent credentials to access systems beyond the agent's intended scope
- Credential stuffing attacks against agent authentication endpoints

**AISM Controls:**

| Control | Pillar | Description |
|---|---|---|
| Secret scanning in all AI outputs for credentials, API keys, tokens | P1 Shield | Prevent agents from inadvertently exposing credentials in outputs |
| GitGuardian or equivalent integration for real-time secret detection | P1 Shield | Catch credential exposure in AI codebases and outputs immediately |
| Credentials stored in secret vaults with regular rotation | P1 Shield | Centralize credential management and enforce rotation schedules |
| Automated NHI discovery across cloud, on-premises, and CI/CD | P1 Shield | Maintain complete visibility of all machine identities |
| RBAC for all NHI entities | P1 Shield | Enforce least-privilege access for every machine identity |
| Just-in-time privilege elevation | P1 Shield | Grant elevated permissions only when needed, not persistently |
| Automated decommissioning of inactive NHI (more than 90 days) | P1 Shield | Remove credentials for inactive agents before they become attack vectors |
| Dedicated NHI logging channels with real-time anomaly detection | P2 Ledger | Monitor machine identity activity separately with tailored anomaly thresholds |
| Automated alerts on NHI credential misuse | P2 Ledger | Alert immediately on anomalous usage patterns from machine identities |
| Automated NHI credential rotation | P3 Circuit Breaker | Rotate agent credentials automatically without manual intervention |
| Service account disabling with certificate revocation | P3 Circuit Breaker | Rapidly revoke agent credentials when compromise is suspected |
| NHI privilege elevation requires human review | P4 Command Center | Ensure human oversight of any privilege escalation for machine identities |

**MITRE ATLAS:** No current dedicated NHI techniques; monitoring for addition
**OWASP LLM:** LLM06 (Sensitive Information Disclosure)

---

## T6: Runaway Autonomy

**What it is:** Agent behavior that exceeds intended operational boundaries, consuming excessive resources, taking unauthorized actions, or executing recursive workflows without termination. This is not always the result of an attack. It can emerge from legitimate agent goals pursued without adequate constraints.

**Why it is especially dangerous for agents:** An agent with broad tool access and a runaway goal can cause significant harm in a short time. Resource consumption, unauthorized API calls, data modifications, and downstream service impacts can occur faster than human observers can respond without automated containment. ACT-3 and ACT-4 deployments — autonomous and orchestrator tiers — represent the highest runaway risk profile because they operate with post-hoc human review and can spawn other agents.

**Attack vectors:**
- Prompt injection that triggers resource-intensive recursive behaviors
- Goal misspecification causing agents to pursue proxy objectives at scale
- Orchestrator failure leaving worker agents without coordination
- Rate limit bypass through parallel agent spawning
- Tool call loops where one tool invocation triggers another in a cycle
- Delegation chain exploitation: using CP.9 hop limits as a vector by spawning at maximum permitted depth

**AISM Controls:**

| Control | Pillar | Description |
|---|---|---|
| Rate limiting on all API calls, model invocations, and agent actions | P3 Circuit Breaker | Hard limits on action frequency regardless of agent goal state |
| Agent recursion limit governor (F3.2, v3.0) | P3 Circuit Breaker | Hard cap on tool-calling depth enforced at the API gateway layer — not the system prompt; default maximum 4; fail-closed |
| Kill switches accessible to operators with escalation procedures | P3 Circuit Breaker | Multiple activation paths for emergency agent termination |
| Redundant kill switches: hardware and software with multi-stage shutdown | P3 Circuit Breaker | Defense-in-depth for containment; no single point of failure in shutdown capability |
| Swarm quorum abort mechanism (F3.3, v3.0) | P3 Circuit Breaker | Decentralized threshold-based abort: when a configurable quorum of swarm agents agree the task should stop, coordinated shutdown proceeds without a centralized kill signal |
| Blast radius containment via compartmentalization | P3 Circuit Breaker | Limit the scope of impact from any single runaway agent |
| Circuit breakers with graceful degradation paths | P3 Circuit Breaker | Reduce autonomy before full shutdown when possible |
| Real-time performance dashboards for all production AI systems | P4 Command Center | Detect resource consumption anomalies before they become incidents |
| Anomaly detection with automated alerting | P4 Command Center | Alert on unexpected action rates, tool invocation patterns, or resource usage |
| Token usage and cost tracking across all AI systems | P4 Command Center | Detect runaway behavior through economic signals |
| **CP.8 Catastrophic Risk Threshold Controls** | **CP Governance OS** | **Documents behavioral indicators that trigger emergency suspension regardless of business continuity impact — unauthorized compute acquisition, communication outside approved list, weaponizable capability; required for ACT-3/ACT-4 deployment approval** |
| **CP.10 HEAR Doctrine** | **CP Governance OS** | **Named Human Ethical Agent of Record with cryptographic signing key and unilateral kill-switch authority for all ACT-3/ACT-4 deployments; Class-H actions (irreversible, financially material, security-control-modifying) require HEAR signature before execution; fail-closed — no automatic approval path** |

**MITRE ATLAS:** AML.T0040 (Exploit Public-Facing Application)
**OWASP LLM:** LLM04 (Denial of Service), LLM08 (Excessive Agency)

---

## T7: Data Exfiltration

**What it is:** Adversarial techniques that cause AI agents to expose sensitive data in their outputs, tool calls, or inter-agent communications. This includes both targeted exfiltration (attempting to extract specific data) and inadvertent disclosure (agents including sensitive data in outputs without adversarial intent).

**AISM Controls:**

| Control | Pillar | Description |
|---|---|---|
| PII/PHI masking and tokenization across all pipelines | P1 Shield | Prevent sensitive data from appearing in agent context or outputs |
| DLP controls with tokenization and pseudonymization | P1 Shield | Data loss prevention enforcement at the Shield layer |
| Secret scanning in all AI outputs | P1 Shield | Detect credentials, API keys, and other secrets in agent outputs before they are sent |
| Data isolation and access boundary enforcement | P1 Shield | Ensure agents can only access data appropriate for their function |
| User interaction logging with prompt and query capture | P2 Ledger | Maintain audit trail of all data exposures for investigation and compliance |
| Semantic execution trace logging (A2.5, v3.0) | P2 Ledger | Captures full agent execution trace — reasoning chain, every tool call with parameters, every memory operation — written to an append-only store the agent cannot modify |
| Decision traceability and provenance documentation | P2 Ledger | Track information flow from input through agent reasoning to output |

**MITRE ATLAS:** AML.T0057
**OWASP LLM:** LLM06 (Sensitive Information Disclosure)

---

## T8: Model Inversion and Extraction

**What it is:** Techniques that use the inference API to reconstruct training data, extract model weights, or clone model behavior. For agents with broad tool access, model extraction can expose proprietary systems, training data, or intellectual property.

**AISM Controls:**

| Control | Pillar | Description |
|---|---|---|
| Rate limiting and IP/role-based API restrictions | P1 Shield | Limit query volume from any single source to impede systematic extraction |
| Whitelist-based tool access with least privilege | P1 Shield | Minimize the surface area available for extraction attempts |
| API usage quota monitoring with anomaly alerts | P4 Command Center | Detect systematic querying patterns characteristic of extraction attacks |
| Behavioral baseline anomaly detection | P2 Ledger | Alert on query patterns that deviate from normal usage |

**MITRE ATLAS:** AML.T0005 (Backdoor ML Model)
**OWASP LLM:** LLM10 (Model Theft)

---

## T9: Adversarial Inputs

**What it is:** Inputs crafted to exploit model-specific vulnerabilities, including homoglyph substitution, invisible character injection, encoding attacks, and other techniques that bypass content filters while achieving adversarial goals.

**AISM Controls:**

| Control | Pillar | Description |
|---|---|---|
| Homoglyph and invisible character injection prevention | P1 Shield | Normalize inputs to detect visually similar but functionally different characters |
| Format normalization before tokenization across all pipelines | P1 Shield | Standardize encoding before inputs reach model tokenization |
| Input encoding validation: UTF-8 enforcement | P1 Shield | Reject inputs with unexpected encoding that may be attempting bypass |
| Toxicity scoring with organizational policy enforcement | P1 Shield | Evaluate inputs against defined content policies |
| Statistical anomaly detection on input data with automated profiling | P1 Shield | Detect statistically unusual inputs that may indicate adversarial crafting |
| Adversarial input fuzzing pipeline (S1.4, v3.0) | P1 Shield | Integrate automated adversarial testing into CI/CD — systematic attack probe battery before every model update and deployment |

**MITRE ATLAS:** AML.T0051, AML.T0057
**OWASP LLM:** LLM01 (Prompt Injection), LLM03 (Training Data Poisoning)

---

## T10: Insider and Operator Threats

**What it is:** Threats originating from within the organization, including operators who abuse their access to AI systems, developers who introduce vulnerabilities intentionally, and governance bypasses that undermine control effectiveness.

**AISM Controls:**

| Control | Pillar | Description |
|---|---|---|
| Tamper-proof, centralized logging with cryptographic signing | P2 Ledger | Ensure audit trails cannot be modified by insiders |
| Dedicated NHI logging channels with real-time anomaly detection | P2 Ledger | Detect insider abuse of machine identities |
| Decision provenance documentation from input to output | P2 Ledger | Create accountability trail for all AI-driven decisions |
| Human approval workflows for critical AI actions | P4 Command Center | Require cross-functional review for high-impact operations |
| Cross-functional AI governance collaboration | P4 Command Center | Distribute governance authority to prevent single-person control |
| Red team and adversarial testing of AI systems | P4 Command Center | Surface insider-accessible vulnerabilities through structured testing |
| Comprehensive operator training with accountability framework | P5 Learning Engine | Build culture of AI accountability with documented expectations |
| Role-based training programs | P5 Learning Engine | Ensure all operators understand their responsibilities and the consequences of violations |
| **CP.1 Agent Failure Mode Taxonomy** | **CP Governance OS** | **Every agentic incident tagged with cognitive_surface=(model\|memory\|both) and memory_persistence=(session\|cross_session) — separates ordinary prompt failures from belief drift and memory corruption; prevents insider incidents from being misclassified as model errors** |

**MITRE ATLAS:** AML.T0010 (Craft Adversarial Data)
**OWASP LLM:** LLM09 (Overreliance), LLM07 (Insecure Plugin Design)

---

## T11: Multi-Turn Behavioral Conditioning *(Added v3.0)*

**What it is:** Attacks that exploit multi-session interaction to gradually modify agent behavior through repeated exposure to crafted inputs. Unlike T1 prompt injection — which attempts a single-turn override — behavioral conditioning operates across many interactions, implanting behavioral patterns that persist across sessions and bypass per-input detection.

**Why it is a distinct threat category:** T1 prompt injection is detectable at the input boundary on a per-message basis. Multi-turn behavioral conditioning is not. It works by changing how an agent interprets future inputs — through few-shot pattern implanting, role confusion across conversations, or systematic bias toward specific responses. Standard injection filters do not detect it because no individual message appears adversarial. Detection requires semantic analysis across multiple sessions and behavioral baseline comparison over time.

**Why it is especially dangerous for agents:** Agents with persistent memory and cross-session context are uniquely susceptible. The attack surface grows with every session the agent maintains. An agent that has been successfully conditioned will continue to behave anomalously even after the attacker stops interacting with it, because the behavior is now part of the agent's learned context rather than an active injection.

**Attack vectors:**
- Few-shot pattern implanting: providing repeated crafted examples across sessions to shift agent decision-making toward attacker-desired outputs
- Role confusion: systematically eroding the agent's understanding of its operational role through incremental reframing across many interactions
- Contextual anchoring: embedding reference points in early sessions that bias the agent's interpretation of later inputs
- Persona drift: gradually shifting the agent's assumed identity through conversational conditioning
- Belief injection: introducing false factual claims that the agent incorporates into its persistent context over time

**AISM Controls:**

| Control | Pillar | Description |
|---|---|---|
| Cognitive injection sanitization (S1.6, v3.0) | P1 Shield | Semantic intent analysis layer that detects multi-turn behavioral conditioning, role confusion, and few-shot pattern implanting across sessions — beyond what pattern-matching filters catch |
| Per-agent session isolation | P1 Shield | Prevent cross-session contamination of agent context; conditioning in one session cannot influence behavior in another |
| Memory governance boundary controls (S1.5, v3.0) | P1 Shield | Authorization required for every write to persistent agent memory — prevents conditioning from persisting without audit trail |
| Behavioral baseline anomaly detection across sessions | P2 Ledger | Alert when agent behavior trends over multiple sessions rather than triggering only on per-input anomalies |
| Semantic execution trace logging (A2.5, v3.0) | P2 Ledger | Cross-session reasoning chain capture enables retrospective analysis of conditioning progression |
| RAG corpus diff tracking (A2.6, v3.0) | P2 Ledger | Identifies when conditioning has succeeded in altering retrieved context rather than just immediate outputs |
| Behavioral drift baseline and rollback (F3.4, v3.0) | P3 Circuit Breaker | Establishes measurable behavioral baselines; automated rollback when drift exceeds configurable thresholds — catches successful conditioning before it becomes entrenched |
| Context consistency verification | P4 Command Center | Monitor for cross-session context anomalies that may indicate active conditioning campaign |
| **CP.2 Adversarial ML Threat Model Integration** | **CP Governance OS** | **Mandatory governance artifact for ACT-2+ deployments mapping every threat with temporal_profile=(immediate\|delayed_days\|delayed_weeks\|chronic) — explicitly designed to capture time-shifted attacks like behavioral conditioning campaigns** |

**MITRE ATLAS:** No current dedicated technique; closest is AML.T0051 (Prompt Injection) — monitoring for dedicated T11-class technique addition
**OWASP LLM:** LLM01 (Prompt Injection) — behavioral conditioning not yet explicitly categorized

---

## Threat Coverage by AISM Pillar

| Threat Category | P1 Shield | P2 Ledger | P3 Circuit Breaker | P4 Command Center | P5 Learning Engine | CP Governance OS |
|---|---|---|---|---|---|---|
| T1: Prompt Injection | Primary | Supporting | None | Supporting | Continuous improvement | CP.7 deception layer |
| T2: Multi-Agent Exploitation | Primary | Supporting | Primary | Primary | Red team | CP.4 control plane, CP.9 replication governance |
| T3: Memory Poisoning | Primary | Primary | Primary | Supporting | Research integration | CP.7 RAG canaries |
| T4: Supply Chain Compromise | Primary | Primary | None | Supporting | Threat intelligence | CP.5 platform profiles |
| T5: NHI Abuse | Primary | Primary | Primary | Primary | Training | None |
| T6: Runaway Autonomy | None | Supporting | Primary | Primary | Red team | CP.8 catastrophic thresholds, CP.10 HEAR |
| T7: Data Exfiltration | Primary | Primary | None | Supporting | Awareness | None |
| T8: Model Extraction | Supporting | Primary | None | Primary | None | None |
| T9: Adversarial Inputs | Primary | Supporting | None | None | Continuous improvement | None |
| T10: Insider Threats | None | Primary | None | Primary | Primary | CP.1 failure taxonomy |
| T11: Behavioral Conditioning | Primary | Primary | Supporting | Supporting | None | CP.2 threat model |

---

## Using This Matrix

**For red teams:** Use the threat categories and attack vectors as the basis for adversarial test scenarios. Every attack vector listed here should have a corresponding red team exercise. Coverage gaps in the AISM self-assessment will indicate which threats are least likely to be detected. T11 requires multi-session red team exercises, not single-interaction tests.

**For security architects:** Use the control columns to verify that specific threats are addressed in your AISM pillar implementations. A control appearing in this matrix that is not implemented in your environment is a documented gap. CP Governance OS controls are cross-pillar and should be verified separately from pillar-level controls.

**For compliance teams:** Use the MITRE ATLAS and OWASP LLM cross-references to map threat coverage to threat framework requirements. Note that T5 (NHI Abuse) and T11 (Behavioral Conditioning) currently have limited MITRE ATLAS coverage — CSI is tracking both for technique addition in upcoming Atlas updates.

**For governance leaders:** Use the threat category overview to understand the agentic threat landscape and prioritize governance investment in the areas of highest organizational exposure. CP.8 Catastrophic Risk Thresholds and CP.10 HEAR Doctrine are deployment blockers for ACT-3 and ACT-4 systems — their absence constitutes an undocumented organizational risk acceptance.

---

## Related Documents

- [operational-loop.md](./operational-loop.md): How the defense loop stages address each threat category in sequence
- [control-stack.md](./control-stack.md): Where specific controls live in the technical architecture
- [AISM-Compliance-Crosswalk.md](./AISM-Compliance-Crosswalk.md): How threat controls map to regulatory framework requirements
- [AISM-Self-Assessment-Tool.md](./AISM-Self-Assessment-Tool.md): The assessment checklist that verifies control implementation against these threats

---

*© 2026 Cyber Strategy Institute. Licensed under CC BY 4.0.*