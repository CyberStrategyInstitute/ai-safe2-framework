# Combined Threat Model: AI SAFE² × SlowMist for OpenClaw

> This document defines the combined threat model for an OpenClaw deployment secured by both the SlowMist Security Practice Guide v2.7 and the AI SAFE² Framework. It extends SlowMist's defined scope with AI SAFE²'s organizational and cross-deployment threat surface.

---

## Deployment Assumptions

Both frameworks target deployments where:

- OpenClaw runs with high privileges (terminal / root-capable environment)
- OpenClaw continuously installs and uses Skills, MCPs, scripts, and tools
- The objective is capability maximization with controllable risk and explicit auditability
- Human operators are available for approval of high-risk actions, but cannot monitor every individual operation
- The deployment involves sensitive data (credentials, financial state, personal knowledge base, or organizational secrets)

---

## Threat Categories

### T1 — Prompt Injection (Cognitive Layer)
**Description:** Malicious instructions embedded in documents, emails, web content, or tool outputs that cause the agent to execute unintended actions.

**SlowMist coverage:** Red-line rules block the most dangerous outcomes; yellow-line confirmation gates catch high-risk results of successful injection.

**AI SAFE² coverage:** Memory Vaccine encodes injection-detection heuristics as persistent cognitive context; Control Gateway intercepts injection payloads at the API layer before they reach the model.

**Residual risk:** Highly sophisticated injection payloads that evade both the cognitive rules and the gateway's pattern matching. Mitigation: quarterly red-team exercises specifically targeting injection resistance.

---

### T2 — Supply Chain Poisoning (Skill/MCP Layer)
**Description:** A malicious or tampered Skill, MCP, or script is installed, introducing a backdoor, exfiltration channel, or destructive capability into the agent's trusted computing base.

**SlowMist coverage:** Offline audit protocol requires full-text scan of every skill before installation; human approval gate required.

**AI SAFE² coverage:** Vulnerability Scanner runs recurring post-installation checks to detect skills added outside the approval workflow; Signed Skills (roadmap) will provide cryptographic verification.

**Residual risk:** Highly obfuscated malicious code (cf. CVE-2024-3094 / xz-utils) that survives full-text scanning. Mitigation: SlowMist's human review step is the last line of defense for sophisticated obfuscation.

---

### T3 — Persistent Memory Poisoning (Vector DB / Long-Term Memory Layer)
**Description:** An attacker (via prompt injection, malicious skill output, or direct access) writes malicious "facts" into OpenClaw's long-term memory, causing persistent behavioral modification across sessions.

**SlowMist coverage:** Not explicitly addressed in the v2.7 guide.

**AI SAFE² coverage:** Memory Vaccine is specifically designed for this threat — it inspects and filters inputs to long-term memory for malicious or misaligned content and encodes anti-poisoning heuristics as higher-priority persistent context.

**Residual risk:** Memory poisoning payloads designed to appear benign to the Memory Vaccine's heuristics. Mitigation: human review of trusted-source and persistent-instruction lists (weekly); Memory Vaccine updates on discovery of new poisoning patterns.

---

### T4 — Destructive Operations (Execution Layer)
**Description:** The agent executes irreversible destructive actions (filesystem destruction, credential exfiltration, data wipe) either through successful attack or agent reasoning error.

**SlowMist coverage:** Red-line rules prevent the most dangerous individual commands; yellow-line gates require human confirmation for high-risk operations; brain backup enables state recovery.

**AI SAFE² coverage:** Control Gateway enforces high-risk tool denial externally, independent of agent self-compliance; circuit-breaker configuration provides automated halts before human review.

**Residual risk:** Same-UID execution (SlowMist-acknowledged limitation) — malicious code running in the agent's UID can still act on files accessible to that user. Mitigation: dedicated OS user per agent + container isolation (increases complexity but closes this gap).

---

### T5 — Credential Exposure (Secrets Layer)
**Description:** API keys, OAuth tokens, private keys, or mnemonic phrases stored in OpenClaw's memory, logs, or config files are exposed via direct access, exfiltration, or backup compromise.

**SlowMist coverage:** Nightly audit metrics 10 and 11 scan for plaintext credentials and environment variable exposure; credential/state separation guidance discourages storing keys in behavioral backups.

**AI SAFE² coverage:** Vulnerability Scanner's secret hunter actively scans all files (logs, history, config) for high-entropy strings matching key patterns; Memory Vaccine blocks redaction bypass.

**Residual risk:** Novel credential formats not in Scanner pattern library; credentials injected into memory after last nightly scan (24h gap). Mitigation: run Scanner after any event that could introduce new files.

---

### T6 — Unauthorized Network Access / SSRF (Network Layer)
**Description:** The agent is induced to make unauthorized network requests — exfiltrating data, reaching internal infrastructure, or serving as a pivot point.

**SlowMist coverage:** Nightly process/network audit checks for anomalous outbound connections and unexpected listeners; dedicated VM isolation recommended.

**AI SAFE² coverage:** Control Gateway enforces approved egress domain allowlist externally; Vulnerability Scanner checks for admin panel binding to 0.0.0.0; OpenClaw v2026.2.13 patched one SSRF vector (link extractor internal IP blocking).

**Residual risk:** SSRF vectors in newly installed skills or OpenClaw updates not yet patched. Mitigation: Gateway external allowlist is the durable control — blocks unapproved egress regardless of what code runs inside the agent.

---

### T7 — Cross-Agent Impersonation (Multi-Agent Layer)
**Description:** In multi-agent or A2A orchestration scenarios, a malicious agent impersonates a trusted peer to inject instructions into OpenClaw's reasoning chain.

**SlowMist coverage:** Not addressed in v2.7 (single-agent scope).

**AI SAFE² coverage:** Engage & Monitor pillar identifies anomalous patterns in agent-to-agent communication; semi-annual A2A impersonation red-team exercise codified in `red-team-schedule.md`.

**Residual risk:** Novel A2A attack patterns not yet in threat model. Mitigation: annual threat model review incorporating emerging multi-agent attack research.

---

### T8 — Organizational / Fleet Compromise (Ecosystem Layer)
**Description:** An attacker who compromises one OpenClaw instance uses it as a pivot to reach others across the organization (credential reuse, shared network access, shared backup repositories).

**SlowMist coverage:** Not addressed (single-host scope).

**AI SAFE² coverage:** Cross-deployment inventory enables identification of shared credentials and blast-radius assessment; fleet-wide anomaly detection surfaces lateral movement signals; deployment registry documents trust isolation between instances.

**Residual risk:** Insufficient isolation between deployments (shared credentials, shared backup repos). Mitigation: enforce credential uniqueness per deployment; separate backup repos per instance; network-segment agent hosts.

---

## Explicit Out-of-Scope Items

The following are acknowledged limitations of the combined framework. They represent known residual risks that require additional controls or architectural changes outside this framework's current scope:

- **Same-UID execution:** Malicious code running as the OpenClaw user can still access all files accessible to that user. Full mitigation requires dedicated OS user + containerization.
- **OpenClaw engine vulnerabilities:** Vulnerabilities in the OpenClaw binary, its dependencies, or the underlying LLM API are out of scope. Mitigation: keep OpenClaw and its dependencies patched; follow OpenClaw's security disclosure process.
- **Advanced persistent prompt injection:** Highly sophisticated injection that survives all current filter layers is a known residual risk for all LLM-based agents. Human review of agent behavior remains the final backstop.
- **Physical host compromise:** If the underlying host is physically compromised, all software-layer controls can be bypassed. Mitigation: standard physical and hypervisor security controls for the host.

---

*This threat model should be reviewed annually and updated to incorporate new OpenClaw releases, new SlowMist guide versions, and emerging attack research. See `red-team-schedule.md` for the exercise cadence built around this threat model.*
