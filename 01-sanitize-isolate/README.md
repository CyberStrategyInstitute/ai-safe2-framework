# Pillar 1: Sanitize & Isolate (P1)
### 🛡️ The First Line of Defense

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Layer](https://img.shields.io/badge/Layer-Pillar_1-820F1A?style=flat-square)](./README.md)
[![Status](https://img.shields.io/badge/Status-Current-808080?style=flat-square)](../EVOLUTION.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

**Previous:** Framework Home | **Next:** [Pillar 2: Audit & Inventory →](../02-audit-inventory/README.md)

---

## 🎯 The Problem. The Realization. The Solution.

**Problem:** AI agents process inputs from everywhere: users, retrieved documents, tool outputs, emails, web pages, API responses. Every one of these is a potential injection surface. Most defenses check only what the user typed. Attackers know this. They embed instructions in documents the agent will retrieve, in tool responses, in content the agent scrapes. By the time the agent acts on those instructions, the injection is invisible in the logs.

**Realization:** The input boundary for an agentic system is not the chat box. It is every surface the agent reads, writes to, and reasons about, including its own persistent memory. Memory that an agent can write to with no governance becomes a slow-moving attack surface that corrupts future behavior across every interaction that follows.

**Solution:** Pillar 1 defines the complete sanitization and isolation perimeter for agentic AI. It covers every input channel, every memory write boundary, every execution environment, and every protocol connection. Clean inputs and bounded execution are what produce consistent, predictable agent behavior.

> **What you get:** Agents that stay on-task, resist manipulation, produce reproducible outputs, and do not accumulate corrupted beliefs over time.

---

## 🏗️ Topic 1: Sanitize (P1.T1)
*Input Validation, Data Filtering, Cleansing*

### Core Controls (v2.0)

- **[P1.T1.1] Input Validation & Schema Enforcement:** Validate inputs against schemas; reject malformed formats; enforce type checking and content-length restrictions.
- **[P1.T1.2] Malicious Prompt Filtering:** Detect and block prompt injection (OWASP LLM01); implement adversarial detection; monitor for jailbreaks.
- **[P1.T1.3] Data Quality Checks:** Validate integrity; detect statistical anomalies and outliers; flag corrupted data.
- **[P1.T1.4] Toxic Content Detection:** Screen for harmful content; implement toxicity scoring; filter based on policy.
- **[P1.T1.5] Sensitive Data Masking (PII/PHI):** Auto-detect and mask PII; redact PHI (HIPAA); implement DLP controls; tokenize sensitive fields.
- **[P1.T1.6] Format Normalization:** Standardize input formats; validate character encodings (UTF-8); prevent encoding attacks.
- **[P1.T1.7] Dependency Verification:** Validate software dependencies; maintain SBOMs; cross-reference CVE databases.
- **[P1.T1.8] Encoding Validation:** Enforce normalization forms (NFKC); prevent homoglyph and encoding-based attacks.
- **[P1.T1.9] Supply Chain Artifact Validation:** Cryptographically verify model and dataset authenticity; validate checksums (SHA-256).

### 🚀 v2.1 Advanced Gap Fillers

- **[P1.T1.2_ADV] Supply Chain Artifact Validation:**
  - **OpenSSF Model Signing (OMS):** Cryptographic model verification using Sigstore/Cosign
  - **SBOM Validation:** Validate Software Bill of Materials against actual dependencies
  - **Provenance Chain:** Trace model lineage from base to deployment
  - **Model Fingerprinting:** SHA-256 hash enforcement to prevent tampering

- **[P1.T1.4_ADV] NHI Secret Validation:**
  - **Secret Scanning:** Detect embedded credentials and tokens in AI outputs
  - **GitGuardian Integration:** Real-time secret detection in code and logs

- **[P1.T1.5_ADV] Memory-Specific Attack Mitigation:**
  - **Cryptographic Memory Fingerprinting:** SHA-256 hashing of agent state
  - **Thread Injection Prevention:** Isolate and sanitize interaction history per principal or request context
  - **Semantic Similarity Analysis:** Detect gradual poison patterns in RAG

### ⚡ v3.0 New Controls

> These controls were introduced in v3.0 and remain part of the current [AI SAFE² v3.1 framework](../README.md). Current implementation resources are available through the [AI SAFE² toolkit](https://cyberstrategyinstitute.com/ai-safe2/).

| Control | Name | Priority | What It Solves |
| :--- | :--- | :--- | :--- |
| **[P1.T1.10]** | Indirect Injection Surface Coverage | 🔴 CRITICAL | Enumerates every non-prompt input channel (docs, tool outputs, emails, APIs) as a sanitization surface, not just user input |
| **[S1.3]** | Semantic Isolation Boundary Enforcement | 🔴 CRITICAL | Prevents cross-agent context contamination; trusted instructions and untrusted content are architecturally separated |
| **[S1.4]** | Adversarial Input Fuzzing Pipeline | 🟠 HIGH | Integrates automated adversarial testing into CI/CD before every deployment, finding breakpoints before users do |
| **[S1.5]** | Memory Governance Boundary Controls | 🔴 CRITICAL | Every write to persistent agent memory requires authorization, sanitization, and an audit log entry |
| **[S1.6]** | Cognitive Injection Sanitization | 🟠 HIGH | Detects semantic-level bypass techniques: multi-turn conditioning, role confusion, few-shot pattern implanting |
| **[S1.7]** | No-Code / Low-Code Platform Security | 🔴 CRITICAL | Governs n8n, Zapier, Power Automate, and comparable automation attack surfaces |

---

## 🏗️ Topic 2: Isolate (P1.T2)
*Containment, Sandboxing, Boundary Enforcement*

### Core Controls (v2.0)

- **[P1.T2.1] Agent Sandboxing:** Deploy agents in isolated environments; implement resource limits (CPU/RAM); use containerization.
- **[P1.T2.2] Network Segmentation:** Isolate AI workloads in dedicated VLANs; use firewalls and ACLs to restrict traffic.
- **[P1.T2.3] API Gateway Restrictions:** Deploy gateways with auth; implement rate limiting; restrict access by IP/Role.
- **[P1.T2.4] Model Versioning:** Maintain separate environments for versions; isolate production from development.
- **[P1.T2.5] Function Access Control:** Restrict agent access to tools; implement allowlisting; use least privilege.
- **[P1.T2.6] Data Isolation:** Separate sensitive data; implement access controls; encrypt at rest and in transit.
- **[P1.T2.7] Container Security:** Harden images; scan for vulnerabilities; implement runtime monitoring.
- **[P1.T2.8] Firewall Controls:** Deploy NGFWs; implement IDS/IPS; enforce egress filtering.
- **[P1.T2.9] Credential Compartmentalization:** Store API keys in secure vaults; rotate regularly.

### 🚀 v2.1 Advanced Gap Fillers

- **[P1.T2.1_ADV] Multi-Agent Boundary Enforcement:**
  - **Agent Network Segmentation:** Isolate Agent-to-Agent (A2A) communications
  - **Quarantine Procedures:** Automatically isolate agents exhibiting anomalies
  - **P2P Trust Scoring:** Reputation weighting for inter-agent trust

- **[P1.T2.2_ADV] NHI Access Control:**
  - **NHI Enumeration:** Catalog all service accounts and agents
  - **Least Privilege:** Assign minimum permissions to NHI entities
  - **Automated Decommissioning:** Remove stale and unused NHI credentials

---

## 📊 Pillar 1 GRC Mapping

| Framework | Control | Mapping |
| :--- | :--- | :--- |
| OWASP LLM Top 10 | LLM01 Prompt Injection | P1.T1.2, P1.T1.10, S1.3, S1.6 |
| OWASP AIVSS v0.8 | Risk #1 Tool Misuse | P1.T1.10, S1.3, M4.5 |
| MITRE ATLAS | AML.T0051 Prompt Injection | P1.T1.2, S1.6 |
| ISO/IEC 42001 | Sec 8.2.2 | P1.T1 input validation chain |
| HIPAA | PHI Redaction 164.308 | P1.T1.5 |
| SOC 2 | CC.6.1, CC.6.2 | P1.T2 boundary controls |
| CVE-2026-25049 | n8n Sandbox Escape | S1.7 |

---

## 🔗 Navigation

| Previous | Current | Next |
| :--- | :--- | :--- |
| [Framework Home](../README.md) | **Pillar 1: Sanitize & Isolate** | [Pillar 2: Audit & Inventory](../02-audit-inventory/README.md) |

[Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/) | [Toolkit](https://cyberstrategyinstitute.com/ai-safe2/)

---

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
