# 🛡️ Pillar 1: Sanitize & Isolate (Assessment Lite)
**v2.1 Community Edition**

This checklist covers the **critical "Air Lock" controls** required to secure an AI Agent's input and runtime environment.

> **⚠️ NOTE:** This is a manual checklist for **Pillar 1 only**.
> To get the **Full 128-Point Automated Audit Scorecard** (covering Audit, Fail-Safe, Monitoring, and GRC mapping), [**Download the AI SAFE² Implementation Toolkit ($97)**](https://cyberstrategyinstitute.com/AI-Safe2/).

---

## 1.1 Input Sanitization (The "Air Lock")

- [ ] **[P1.T1.1] Schema Enforcement:** Are all agent inputs validated against strict JSON schemas (Pydantic/Zod)?
- [ ] **[P1.T1.2] Prompt Injection Firewall:** Is a middleware scanner (e.g., Rebuff, NeMo) active before the LLM inference?
- [ ] **[P1.T1.5] PII Redaction:** Are Credit Cards, SSNs, and Emails masked before entering the context window?
- [ ] **[P1.T1.2_ADV] Supply Chain Validation:** Do you verify the SHA-256 hash or OpenSSF signature of models before loading?
- [ ] **[P1.T1.4_ADV] Secret Hygiene:** Is there a real-time scanner checking agent outputs for leaked API keys?

## 1.2 Isolation Architectures (The "Cell")

- [ ] **[P1.T2.1] Container Sandboxing:** Do agents run in ephemeral, read-only containers (e.g., gVisor, Firecracker)?
- [ ] **[P1.T2.2] Network Egress:** Is the default network policy "Deny-All" with an explicit whitelist?
- [ ] **[P1.T2.5] Tool Whitelisting:** Does the agent have a restricted set of allowed tools (no `rm -rf` or unrestricted shell)?
- [ ] **[P1.T2.1_ADV] Swarm Segmentation:** Are "Planner" agents network-isolated from "Executor" agents?
- [ ] **[P1.T2.2_ADV] NHI Access Control:** Does the agent use a dedicated Service Account (not a user identity)?

---

### 🚦 Score Your Results
*   **0-5 Checked:** 🚨 **CRITICAL RISK.** Your agents are vulnerable to trivial injection attacks.
*   **6-9 Checked:** 🟠 **AT RISK.** You have basic hygiene but lack advanced agentic hardening.
*   **10 Checked:** 🟢 **SECURE.** You are ready to audit Pillar 2 (Inventory & Audit).

👉 **[Get the Full Framework & Automated Scorecard Here](https://cyberstrategyinstitute.com/AI-Safe2/)**
