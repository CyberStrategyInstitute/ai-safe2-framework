# SAFE²-for-SlowMist Overlay
## Mapping the SlowMist OpenClaw Security Practice Guide into the AI SAFE² Five-Pillar Framework

> **Purpose:** This one-pager is a companion reference for operators who have deployed (or are deploying) the SlowMist OpenClaw Security Practice Guide and want to understand how each control maps into the AI SAFE² Framework's five pillars — and exactly where the Memory Vaccine, Vulnerability Scanner, and Control Gateway should sit in the SlowMist control flow.

---

## Control Mapping: SlowMist → AI SAFE² Five Pillars

### Pillar 1 — Sanitize & Isolate

*AI SAFE² Goal: Minimize the agent's attack surface before and during execution. Scope credentials. Isolate workloads. Sanitize LLM inputs.*

| SlowMist Control | Phase | AI SAFE² Alignment |
|---|---|---|
| Behavioral Red Lines (never `rm -rf /`, never blindly execute hidden instructions) | Pre-action | Hardcoded execution boundaries; prevents unsanitized prompt content from driving destructive actions |
| Behavioral Yellow Lines (pause on `sudo`, SSH key ops, financial transactions) | Pre-action | Human-in-the-loop gate for high-risk operations; scoped permission enforcement |
| Skill Installation Audit (offline clone → full-text scan → human approval) | Pre-action | Supply-chain sanitization; blocks malicious code before it enters the trusted computing base |
| Permission Narrowing (agent self-constrains file and process permissions) | In-action | Least-privilege execution; limits blast radius of compromise |
| Dedicated VM / isolated host recommendation | Deployment | Workload isolation; separates agent trust boundary from host user trust boundary |

**🔧 Memory Vaccine placement:** Deploy *within* this pillar. The Memory Vaccine acts as the always-on sanitization layer for OpenClaw's vector memory — it blocks malicious or misaligned content from being written to long-term memory, complements the pre-action red-line taxonomy by encoding it as persistent cognitive context, and catches prompt injection payloads that survive the pre-action behavioral filters.

---

### Pillar 2 — Audit & Inventory

*AI SAFE² Goal: Know what automations are running, what privileges they hold, and what they touched. Make all of this independently verifiable.*

| SlowMist Control | Phase | AI SAFE² Alignment |
|---|---|---|
| Nightly 13-Metric Audit (platform scan, processes, directory changes, cron integrity, SSH failures, hash baseline, yellow-line counts, disk, env vars, credential scan, skill baseline, backup) | Post-action | Reference implementation for the Inventory pillar; covers host-level posture across the full attack surface |
| Hash Baseline Verification (critical configs tracked nightly) | In-action / Post-action | Configuration integrity inventory; detects unauthorized drift |
| Skill Baseline Check (extension directory audit) | Post-action | Supply-chain inventory; detects skill additions outside the approval workflow |
| Audit Log with `chattr +i` (immutable attributes on logs) | In-action | Tamper-evident audit trail; supports forensic reconstruction |
| Yellow-Line Count vs. Memory Log Cross-Reference | Post-action | Behavioral inventory; detects discrepancy between agent self-report and external observation |

**🔧 Vulnerability Scanner placement:** Deploy *within* this pillar, as a scheduled complement to SlowMist's nightly audit cron. Run `scanner.py` on the same schedule or on-demand after skill installations. The Scanner surfaces secrets exposure, permission misconfigurations, and admin panel exposure that the nightly audit script doesn't cover. Together they provide 360° host-layer inventory coverage.

**Audit gap SlowMist doesn't close:** SlowMist audits one host. AI SAFE²'s Audit & Inventory pillar requires an enterprise-wide automation registry. Operators with multiple OpenClaw deployments should extend the nightly audit output into a centralized log aggregator (e.g., a SIEM or a shared private repo) to achieve cross-deployment visibility.

---

### Pillar 3 — Fail-Safe & Recovery

*AI SAFE² Goal: Ensure the system degrades safely, recovers predictably, and limits irreversible outcomes when controls fail.*

| SlowMist Control | Phase | AI SAFE² Alignment |
|---|---|---|
| Human Confirmation for High-Risk Actions (irreversible/sensitive ops pause) | In-action | Circuit-breaker pattern; prevents autonomous execution of irreversible operations |
| Brain Backup to Private Repo (OpenClaw state directory pushed nightly) | Post-action | Behavioral state recovery; enables rollback to known-good cognitive context |
| Credential/State Separation (explicit guidance to separate keys from behavioral state) | Deployment | Limits blast radius of credential compromise during recovery |
| Explicit Push Notification on Audit Completion | Post-action | Confirms the recovery mechanism itself is functioning; surfaces silent failures |
| Report persistence at `/tmp/openclaw/security-reports/` | Post-action | Local fallback when push delivery fails; ensures audit record is never lost |

**AI SAFE² extensions to add:** SlowMist's Fail-Safe controls operate reactively (confirm before action, backup nightly). AI SAFE² adds *automated* circuit breakers at the Control Gateway layer — proactive trip-wires that halt execution when behavioral risk scores exceed thresholds, before a human even sees the alert. Operators should treat the nightly confirmation push as the detection layer and the Gateway as the prevention layer.

---

### Pillar 4 — Engage & Monitor

*AI SAFE² Goal: Maintain real-time visibility into agent behavior. Detect anomalies, poisoning attempts, and abuse before they become incidents.*

| SlowMist Control | Phase | AI SAFE² Alignment |
|---|---|---|
| Cross-Skill Pre-flight Business Risk Checks | In-action | Runtime behavioral monitoring; catches business-logic abuse before execution |
| Nightly Process/Network Audit (anomalous outbound connections, unexpected listeners) | Post-action | Network behavioral monitoring; detects exfiltration channels |
| Yellow-Line Audit Count (sudo usage tracked and cross-referenced) | Post-action | Privilege-use monitoring; surfaces privilege escalation patterns |
| SSH Failure Count Monitoring | Post-action | Authentication anomaly detection |
| Sensitive Credential Scanning (memory/ dirs scanned for plaintext keys, mnemonics) | Post-action | Data-at-rest exposure monitoring |

**🔧 Control Gateway placement:** Deploy *within* this pillar, inline between OpenClaw and the LLM API. The Gateway is the real-time monitoring and enforcement layer that SlowMist's post-action audit cannot provide: it sees every request, applies a 0–10 risk score per call, blocks prompt injection patterns in real time, and writes immutable API-layer audit logs. This closes the 24-hour detection latency gap that SlowMist explicitly acknowledges in its hash baseline limitations ("maximum discovery latency of ~24h").

**Monitoring gap SlowMist doesn't close:** Cross-agent behavioral correlation. If an attacker poisons one OpenClaw instance to behave abnormally, SlowMist's per-box audit will eventually surface it. AI SAFE²'s Engage & Monitor pillar extends detection to *patterns across instances* — coordinated anomalies, timing correlations, and behavioral drift that only appear when you view the fleet.

---

### Pillar 5 — Evolve & Educate

*AI SAFE² Goal: Keep the security model current. Run adversarial exercises. Train humans. Update threat models as the agent and ecosystem evolve.*

| SlowMist Control | Phase | AI SAFE² Alignment |
|---|---|---|
| Security Validation & Red Teaming Guide (end-to-end defense testing, cognitive injection → host escalation → exfiltration → persistence → audit tampering → recovery) | Ongoing | Reference red-team curriculum; tests all three defense layers operationally |
| Agent-Native Deployment (agent reads, evaluates, and deploys its own defense matrix) | Deployment | Organizational learning model; reduces human configuration error and builds operator intuition |
| FAQ and Boundary Documentation (explicit threat model scope, known limitations) | Ongoing | Threat model documentation; keeps operators calibrated on what the guide does and doesn't protect |

**AI SAFE² extensions to add:** SlowMist provides excellent red-team test cases but doesn't codify a *recurring schedule* for adversarial exercises. AI SAFE²'s Evolve pillar specifies:

- Quarterly RAG leakage drills (test whether poisoned content can influence agent behavior via memory retrieval)
- Semi-annual A2A impersonation exercises (test whether one agent can be induced to trust another malicious agent)
- Annual threat model review incorporating new OpenClaw releases and emerging attack techniques
- Organizational training to keep all operators current on new attack paths documented in the SlowMist validation guide

---

## Tool Placement in the SlowMist Control Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SLOWMIST DEFENSE MATRIX                          │
│                                                                     │
│  PRE-ACTION                                                         │
│  ┌───────────────────────────────────────────────────────┐         │
│  │  Red/Yellow Line Behavioral Rules                      │         │
│  │  Skill Installation Audit (offline → scan → approve)  │         │
│  │                                                        │         │
│  │  ◀── MEMORY VACCINE (AI SAFE² Pillar 1)               │         │
│  │      • Encodes red-line rules as persistent context    │         │
│  │      • Blocks malicious writes to vector memory        │         │
│  │      • Catches prompt injection before pre-flight      │         │
│  └───────────────────────────────────────────────────────┘         │
│                           │                                         │
│  IN-ACTION                ▼                                         │
│  ┌───────────────────────────────────────────────────────┐         │
│  │  Permission Narrowing + Hash Baseline                  │         │
│  │  Business Pre-flight Risk Checks                       │         │
│  │  Audit Logging (immutable)                            │         │
│  │                                                        │         │
│  │  ◀── CONTROL GATEWAY (AI SAFE² Pillar 4)              │         │
│  │      • Sits between OpenClaw ↔ LLM API                │         │
│  │      • Real-time risk scoring (0–10 per request)       │         │
│  │      • Blocks high-risk tool calls externally          │         │
│  │      • Prompt injection interception                   │         │
│  │      • Immutable API-layer audit log                   │         │
│  └───────────────────────────────────────────────────────┘         │
│                           │                                         │
│  POST-ACTION              ▼                                         │
│  ┌───────────────────────────────────────────────────────┐         │
│  │  Nightly 13-Metric Audit + Push Notification          │         │
│  │  Brain Backup to Private Repo                          │         │
│  │  Explicit Report Persistence                           │         │
│  │                                                        │         │
│  │  ◀── VULNERABILITY SCANNER (AI SAFE² Pillar 2)        │         │
│  │      • Runs on same nightly schedule (or on-demand)    │         │
│  │      • Secret scanning across all files               │         │
│  │      • Network exposure check (0.0.0.0 bindings)       │         │
│  │      • Permission audit (root execution, world-read)   │         │
│  │      • 0–100 risk score with remediation steps         │         │
│  └───────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Gap Summary: What the Overlay Adds

| Gap in SlowMist (standalone) | AI SAFE² Control That Closes It |
|---|---|
| 24-hour hash baseline detection latency | Control Gateway (real-time, external) |
| No cross-deployment fleet visibility | Audit & Inventory pillar (centralized aggregation) |
| No identity architecture / credential rotation | Sanitize & Isolate pillar (JIT credentials, rotation bots) |
| Reactive circuit-breakers only (human confirm) | Fail-Safe pillar (automated Gateway trip-wires) |
| Per-box logs, no cross-agent correlation | Engage & Monitor pillar (behavioral analytics fleet-wide) |
| Red-team guide present, no recurring schedule | Evolve pillar (quarterly drills, annual threat model review) |
| No persistent memory sanitization layer | Memory Vaccine (Pillar 1 implementation) |

---

## Quick-Start Deployment Order

For operators who have already deployed the SlowMist guide and want to add the AI SAFE² layer:

1. **Deploy the Memory Vaccine** → add `openclaw_memory.md` to OpenClaw's memory bank. Immediate coverage for cognitive-layer attacks.
2. **Deploy the Control Gateway** → point OpenClaw's API calls through the gateway. Immediate real-time enforcement and API-layer audit logging.
3. **Run the Vulnerability Scanner** → execute `scanner.py` against your OpenClaw data directory. Baseline your current risk score before adding new skills.
4. **Extend the nightly audit** → add the Scanner output to the SlowMist 13-metric report. Route both to a centralized log if running multiple instances.
5. **Schedule red-team exercises** → use SlowMist's Validation Guide as the test curriculum. Cadence: quarterly minimum, after every major OpenClaw release.

---

*This overlay is maintained as a companion document to the AI SAFE² Framework examples/openclaw directory. Cross-reference:*
- *SlowMist guide: [github.com/slowmist/openclaw-security-practice-guide](https://github.com/slowmist/openclaw-security-practice-guide)*
- *AI SAFE² tools: [github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/examples/openclaw](https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/examples/openclaw)*
