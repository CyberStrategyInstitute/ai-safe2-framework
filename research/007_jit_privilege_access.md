<!-- AI-SAFE2-UX:START -->
[![AI SAFE2 v3.1](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Surface: Research](https://img.shields.io/badge/Surface-Research-820F1A?style=flat-square)](./README.md)
[![Context: v3.1 Current](https://img.shields.io/badge/Context-v3.1_Current-808080?style=flat-square)](../docs/REPOSITORY-UX-STANDARD.md)

[Framework Home](../README.md) | [Research Index](./README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

> **Current framework context:** AI SAFE2 v3.1. This research note preserves its original publication date, evidence, and historical framework references. Use current v3.1 normative control and profile documents for implementation or conformance decisions.
<!-- AI-SAFE2-UX:END -->

# Research Note: Just-in-Time (JIT) Privilege for Agents
**ID:** RN-2025-007 | **Related Control:** [P4.T1.2_ADV] | **Status:** Verified

## 🚨 The Threat Vector
**Over-Privileged Agents:** Developers often grant agents "Admin" access to APIs (e.g., GitHub, Jira, AWS) because it is convenient. If the agent is hijacked, the attacker inherits full admin rights.
*   **Research Basis:** *OWASP LLM08: Excessive Agency*.

## 🛡️ The AI SAFE² Solution
We apply **Zero Trust Principles** to Agent permissions.

### 1. The JIT Workflow [P4.T1.2_ADV]
Agents default to "Read-Only."
If an agent needs to perform a "Write" action (e.g., Deploy Code), it must request a **Temporary Token**.
*   **Mechanism:** The agent triggers an approval flow (Slack/Teams). A human approves. The token is minted with a 5-minute TTL (Time To Live).

### 2. Baseline Validation
The request is checked against a "Behavioral Baseline." If a Customer Support agent requests Database Write access, the system auto-rejects it based on role mismatch.

## 📚 References
*   [OWASP Top 10 for LLM](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
*   [Zero Trust Architecture (NIST 800-207)](https://csrc.nist.gov/publications/detail/sp/800-207/final)

<!-- AI-SAFE2-UX-FOOTER:START -->
---

### Research navigation

[Previous research note](./006_runtime_isolation_gvisor.md) | [Research Index](./README.md) | [Next research note](./008_grc_framework_comparison.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [NEXUS](../NEXUS/) | [Challenge Lab](../challenges/)

*AI SAFE2 v3.1 | Cyber Strategy Institute*
<!-- AI-SAFE2-UX-FOOTER:END -->
