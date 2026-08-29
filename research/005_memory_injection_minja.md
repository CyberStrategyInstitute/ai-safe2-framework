<!-- AI-SAFE2-UX:START -->
[![AI SAFE2 v3.1](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Surface: Research](https://img.shields.io/badge/Surface-Research-820F1A?style=flat-square)](./README.md)
[![Context: v3.1 Current](https://img.shields.io/badge/Context-v3.1_Current-808080?style=flat-square)](../docs/REPOSITORY-UX-STANDARD.md)

[Framework Home](../README.md) | [Research Index](./README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

> **Current framework context:** AI SAFE2 v3.1. This research note preserves its original publication date, evidence, and historical framework references. Use current v3.1 normative control and profile documents for implementation or conformance decisions.
<!-- AI-SAFE2-UX:END -->

# Research Note: Indirect Prompt Injection via Memory (MINJA)
**ID:** RN-2025-005 | **Related Control:** [P1.T1.5_ADV], [P5.T1.4_ADV] | **Status:** Verified

## 🚨 The Threat Vector
**Long-Term Memory Poisoning:** Unlike immediate prompt injection, **MINJA (Memory Injection)** attacks target the agent's long-term storage (Vector DB).
*   **Attack:** An attacker emails a benign-looking PDF containing hidden instructions (white text). The agent reads it, stores it in memory. Days later, when asked a question, the agent retrieves the poison and executes the hidden command.
*   **Research Basis:** *MINJA / PajaMAS Research Papers (Q3 2025)*.

## 🛡️ The AI SAFE² Solution
We implement **"Cognitive Hygiene"** protocols for long-term storage.

### 1. Pre-Ingestion Sanitization [P1.T1.5_ADV]
All documents destined for RAG/Memory must be scrubbed of "Control Characters" and adversarial patterns *before* embedding.

### 2. Semantic Drift Detection [P4.T2.3_ADV]
Monitoring the vector space for "Clustering Anomalies." If a new memory chunk sits in a semantic region known for jailbreaks, it is flagged before retrieval.

## 📚 References
*   [ArXiv: Indirect Prompt Injection](https://arxiv.org)
*   [MITRE ATLAS: AML.T0043 Data Poisoning](https://atlas.mitre.org)

<!-- AI-SAFE2-UX-FOOTER:START -->
---

### Research navigation

[Previous research note](./004_supply_chain_model_signing.md) | [Research Index](./README.md) | [Next research note](./006_runtime_isolation_gvisor.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [NEXUS](../NEXUS/) | [Challenge Lab](../challenges/)

*AI SAFE2 v3.1 | Cyber Strategy Institute*
<!-- AI-SAFE2-UX-FOOTER:END -->
