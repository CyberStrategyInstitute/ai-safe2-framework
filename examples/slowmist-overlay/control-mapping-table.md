# Control Mapping Table: SlowMist → AI SAFE² Five Pillars

> **Complete cross-reference:** Every SlowMist OpenClaw Security Practice Guide v2.7 control mapped to its primary AI SAFE² pillar, the tool(s) that implement or extend it, and the gap analysis for what the SlowMist control alone does not close.

---

## Legend

- **Phase:** Pre = Pre-action | In = In-action | Post = Post-action | Dep = Deployment-time
- **Pillar:** S&I = Sanitize & Isolate | A&I = Audit & Inventory | F&R = Fail-Safe & Recovery | E&M = Engage & Monitor | E&E = Evolve & Educate
- **Tool:** MV = Memory Vaccine | VS = Vulnerability Scanner | GW = Control Gateway

---

## Full Mapping Table

| # | SlowMist Control | Phase | AI SAFE² Pillar | Tool(s) | What SlowMist Provides | Gap / AI SAFE² Extension |
|---|---|---|---|---|---|---|
| 1 | Behavioral Red Lines (absolute prohibitions: `rm -rf /`, blind hidden instruction execution, direct credential exfiltration) | Pre | S&I | MV | Cognitive-layer enforcement via agent's own reasoning | MV makes rules persistent across sessions; external Gateway enforces same rules outside agent's cognition layer |
| 2 | Behavioral Yellow Lines (pause + human confirm: `sudo`, SSH key ops, financial transactions, bulk deletion) | Pre | S&I, F&R | GW | Human-in-the-loop gate for high-risk operations | GW adds automated pre-emptive blocking; doesn't require the agent to self-police |
| 3 | Skill Installation Audit (offline clone → full-text scan incl. Markdown/JSON → red-flag check → human approval) | Pre | S&I | VS | Supply-chain intake protocol; blocks malicious code before agent executes it | VS scans existing installed skills on a recurring basis; SlowMist audits at install time only |
| 4 | Permission Narrowing (agent self-constrains file and process permissions to minimum needed) | In | S&I | GW | Least-privilege execution at OS layer | GW enforces least-privilege at the API/tool-call layer independently of agent self-compliance |
| 5 | Hash Baseline for Critical Configs (`openclaw.json`, `sshd_config`, `authorized_keys`) | In / Post | A&I | VS | Configuration integrity; detects unauthorized file drift | VS extends detection to secrets exposure and network bindings that hash comparison misses |
| 6 | Audit Logging with `chattr +i` (immutable log attributes) | In | A&I, E&M | GW | Tamper-evident local audit trail | GW provides a *separate* immutable API-layer audit log outside the agent's filesystem, unaffected by a host compromise |
| 7 | Cross-Skill Pre-flight Business Risk Checks (agent evaluates risk before acting across skill boundaries) | In | E&M | GW | Runtime behavioral monitoring at agent cognition layer | GW performs same check externally at API layer; does not rely on agent's self-assessment |
| 8 | Nightly 13-Metric Audit (platform scan, processes, directory changes, cron integrity, SSH failures, hash baseline, yellow-line counts, disk, env vars, credential scan, skill baseline, backup confirmation) | Post | A&I | VS | Comprehensive host-layer posture assessment | VS runs as a complementary scan (secrets, network exposure, permissions); outputs a risk score for trending; route both to centralized log for multi-deployment view |
| 9 | Push Notification on Audit Completion (Telegram / Discord / Signal) | Post | F&R, E&M | — | Confirms audit pipeline is functioning; surfaces silent failures | Centralized log aggregation enables cross-deployment alert correlation (AI SAFE² E&M) |
| 10 | Report Persistence at `/tmp/openclaw/security-reports/` | Post | F&R | — | Local fallback when push delivery fails | Back up to centralized store for fleet-level retention and forensic availability |
| 11 | Brain Backup to Private Repo (OpenClaw state directory pushed nightly) | Post | F&R | — | Behavioral state recovery; enables rollback to known-good cognitive context | Separate credential rotation and backup per AI SAFE² Fail-Safe pillar; JIT credential issuance limits recovery-time exposure |
| 12 | Credential/State Separation (explicit guidance: don't store keys in behavioral backup) | Dep | F&R, S&I | — | Limits blast radius during recovery | AI SAFE² formalizes this as an identity architecture requirement with automated rotation bots |
| 13 | Dedicated VM / Isolated Host Recommendation | Dep | S&I | — | Workload isolation; trust boundary separation | AI SAFE² extends to container-level isolation policies, network segmentation, and multi-tenant controls |
| 14 | Same-UID Compromise Acknowledgment (documented limitation) | — | S&I | GW | Honest threat model scoping | GW operates *outside* the agent's UID trust boundary; closes this specific gap |
| 15 | Security Validation & Red Teaming Guide (end-to-end test: cognitive injection → host escalation → exfiltration → persistence → audit tampering → recovery) | Ongoing | E&E | — | Comprehensive red-team curriculum covering all three defense tiers | AI SAFE² E&E pillar schedules recurring exercises (quarterly/annual) on this curriculum; SlowMist provides content, AI SAFE² provides cadence |
| 16 | Agent-Native Deployment (agent reads, evaluates, and self-deploys the defense matrix) | Dep | E&E | MV | Reduces human configuration error; builds operator intuition through agent self-assessment | AI SAFE² formalizes as organizational training: operators learn from agent-deployment process |
| 17 | Threat Model Documentation (explicit scope: what the guide does and does not protect) | Dep | E&E | — | Calibrates operator expectations | AI SAFE² E&E requires annual threat model review incorporating new OpenClaw releases and CVEs |

---

## Controls Exclusively in AI SAFE² (No SlowMist Equivalent)

These controls are required for a complete AI SAFE² deployment but have no current equivalent in the SlowMist guide. Operators should treat these as the "overlay" layer that SlowMist alone cannot provide.

| AI SAFE² Control | Pillar | Description | Recommended Implementation |
|---|---|---|---|
| Enterprise-wide automation registry | A&I | Enumerate all OpenClaw deployments, their privilege levels, skills, and data flows | Centralized private repo or SIEM integration aggregating all nightly audit outputs |
| Cross-agent behavioral anomaly correlation | E&M | Detect anomalies that only appear across multiple agent instances (coordinated poisoning, lateral movement) | Ship nightly audit reports + Gateway logs to a unified log aggregator with correlation rules |
| Just-in-time credentials and rotation bots | S&I | Short-lived API keys and OAuth tokens; automated rotation on schedule or on compromise signal | Integrate with secrets manager (HashiCorp Vault, AWS Secrets Manager, etc.) |
| Automated circuit-breakers | F&R | Pre-emptive halt on behavioral risk score threshold breach, without waiting for human review | Control Gateway trip-wire configuration (see gateway/config.yaml) |
| RAG leakage drill | E&E | Quarterly test: can poisoned content influence agent behavior via memory retrieval? | Use SlowMist's cognitive injection test cases as the curriculum; run in isolated test environment |
| A2A impersonation exercise | E&E | Semi-annual test: can one agent be induced to trust a malicious agent impersonating a peer? | Requires multi-agent test environment; scenario design in `red-team-schedule.md` |
| Annual threat model review | E&E | Review threat model against new OpenClaw releases, emerging CVEs, and SlowMist guide updates | Calendar-scheduled; incorporate SlowMist release notes and AI SAFE² framework updates |
| Signed Skills (roadmap) | S&I | Cryptographic verification that skill code hasn't been tampered with since signing | AI SAFE² next release; currently: SlowMist offline audit is the interim control |

---

## Gap Heat Map

| SlowMist Phase | Coverage vs. AI SAFE² Pillar S&I | A&I | F&R | E&M | E&E |
|---|---|---|---|---|---|
| Pre-action | ████████ High | ██ Low | ████ Medium | ██ Low | ████ Medium |
| In-action | ██████ High | ████ Medium | ████ Medium | ██████ Medium-High | ██ Low |
| Post-action | ██ Low | ████████ High | ██████ High | ██████ Medium-High | ████ Medium |
| Deployment | ██████ Medium-High | ██ Low | ████ Medium | ██ Low | ████ Medium |
| Organizational | ██ Low | ██ Low | ██ Low | ██ Low | ████ Medium |

**Interpretation:** SlowMist provides strong coverage of in-agent and post-action controls within its defined scope. AI SAFE² fills the organizational, real-time gateway, and cross-deployment gaps that SlowMist explicitly does not target.

---

*Cross-reference: [`safe2-for-slowmist-overlay.md`](./safe2-for-slowmist-overlay.md) | [`README.md`](./README.md)*
