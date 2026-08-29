<!-- AI-SAFE2-UX:START -->
[![AI SAFE2 v3.1](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Surface: Research](https://img.shields.io/badge/Surface-Research-820F1A?style=flat-square)](./README.md)
[![Context: v3.1 Current](https://img.shields.io/badge/Context-v3.1_Current-808080?style=flat-square)](../docs/REPOSITORY-UX-STANDARD.md)

[Framework Home](../README.md) | [Research Index](./README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

> **Current framework context:** AI SAFE2 v3.1. This research note preserves its original publication date, evidence, and historical framework references. Use current v3.1 normative control and profile documents for implementation or conformance decisions.
<!-- AI-SAFE2-UX:END -->

# Research Note: Non-Human Identity (NHI) Sprawl & Governance
**ID:** RN-2025-002 | **Related Control:** [P1.T1.4_ADV], [P1.T2.2_ADV] | **Status:** Verified

## 🚨 The Threat Vector
**Machine-Identity Explosion:** As enterprises move to Agentic AI, the volume of Non-Human Identities (Service Accounts, API Keys, Bot Tokens) is growing at **100x the rate of human identities**.
*   **Attack:** "Secret Sprawl." Hardcoded credentials in agent code or logs are harvested by attackers to pivot laterally across cloud environments.
*   **Research Basis:** *GitGuardian State of Secrets Sprawl 2025*, *CISA NHI Guidance*.

## 🛡️ The AI SAFE² Solution
Standard IAM controls (designed for humans) fail at machine speed. AI SAFE² v2.1 introduces specific **NHI Governance Controls**:

### 1. Automated Enumeration [P1.T2.2_ADV]
Agents must be treated as "First-Class Citizens" in Identity Providers (IdP). We mandate automated discovery scripts to map every active agent to its specific permissions map.

### 2. Ephemeral Credentials [P5.T1.3_ADV]
Static long-lived API keys are prohibited for Tier 3 Agents.
*   **Implementation:** Use "Just-in-Time" (JIT) token generation via HashiCorp Vault or AWS STS. Keys exist only for the duration of the task.

### 3. Output Hygiene [P1.T1.4_ADV]
Real-time scanning of LLM output streams (using entropy detectors) to ensure an agent does not hallucinate or leak its own configuration secrets to a user.

## 📚 References
*   [GitGuardian: The Machine Identity Crisis](https://blog.gitguardian.com)
*   [CISA: Automated Security for Non-Human Identity](https://cisa.gov)

<!-- AI-SAFE2-UX-FOOTER:START -->
---

### Research navigation

[Previous research note](./001_rag_poisoning.md) | [Research Index](./README.md) | [Next research note](./003_swarm_consensus_failure.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [NEXUS](../NEXUS/) | [Challenge Lab](../challenges/)

*AI SAFE2 v3.1 | Cyber Strategy Institute*
<!-- AI-SAFE2-UX-FOOTER:END -->
