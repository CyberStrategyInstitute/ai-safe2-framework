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
