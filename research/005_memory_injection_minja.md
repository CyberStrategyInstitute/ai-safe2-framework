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
