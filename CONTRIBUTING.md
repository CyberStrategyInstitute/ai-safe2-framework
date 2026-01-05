# Contributing to AI SAFE²

Thank you for your interest in hardening the AI ecosystem. To maintain the integrity of the AI SAFE² Framework as an Enterprise Standard, we adhere to a strict **"Evidence-Based"** contribution process.

We do not accept theoretical ideas without justification. We accept **Engineered Solutions**.

---

## 📋 The Contribution Process

### 1. Identify the Type of Contribution
Are you reporting a bug, or proposing a structural change?
*   **Type A: Gap Analysis:** You found a new threat vector (e.g., a new Jailbreak technique) not covered by the framework.
*   **Type B: New Control:** You have a specific engineering protocol to mitigate a risk.
*   **Type C: Correction:** Fixing a typo, broken link, or outdated reference.

### 2. Open an Issue (The Proposal)
Before submitting a Pull Request (PR), open an Issue using the templates below.

#### 🔴 Template: Gap Analysis (New Threat)
*   **Threat Name:** (e.g., DeepSeek R1 Chain-of-Thought Injection)
*   **The "5 Ws" Justification:**
    *   **Who** is the actor? (Internal dev, external attacker?)
    *   **What** is the attack vector?
    *   **Where** does it happen? (Prompt, RAG, Memory?)
    *   **When** does it occur? (Training, Inference, Retrieval?)
    *   **Why** is current AI SAFE² insufficient?
*   **Evidence/Research:** (Must include links to arXiv papers, CVEs, or PoC code).

#### 🟢 Template: New Control Proposal
*   **Proposed ID:** (e.g., P1.T1.8_ADV)
*   **Control Name:**
*   **Description:** (1-2 sentences).
*   **Technical Check:** (The specific CLI command, Python script, or Logic Check).
*   **Tools Suggested:** (e.g., Garak, Nmap).
*   **Mapping:** (Does this map to NIST, ISO, or MITRE? Cite the specific control ID).

---

## 📝 Example: A Perfect Contribution

If you were submitting a new control for **"RAG Poisoning,"** your issue should look like this:

> **Subject:** New Control Proposal: Context Integrity Hashing
>
> **Justification:** Current controls check input prompts but do not validate the integrity of retrieved RAG documents before they enter the context window. Attackers can poison the Vector DB (MITRE AML.T0043).
>
> **Proposed Control:**
> *   **ID:** P1.T1.5_ADV
> *   **Name:** RAG Context Integrity Verification
> *   **Description:** Calculate SHA-256 hashes of retrieved documents and compare against a trusted allow-list before augmentation.
> *   **Technical Check:** `if hash(retrieved_doc) not in allow_list: raise SecurityError`
> *   **Research/Proof:** See "Poisoned RAG" paper by NVidia (Link).

---

## 🤝 Submission Standards
1.  **Atomicity:** One PR per issue.
2.  **Verification:** If you add a script, it must include a test case.
3.  **Governance:** All contributions are reviewed by the AI Governance Board.

By contributing, you agree to the [Professional Code of Conduct](CODE_OF_CONDUCT.md) and the [Dual License Agreement](LICENSE).
