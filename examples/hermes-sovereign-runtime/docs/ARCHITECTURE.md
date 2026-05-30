# HSR Architecture Reference
### Hermes Sovereign Runtime · AI SAFE² v3.0

---

## Design Philosophy

The HSR rests on one principle: **the security boundary must live outside the agent.**

Hermes Agent's internal controls — approval checks, regex filters, permission gates — are
implemented in Python code the agent can see and that external actors (via leaked source,
reverse engineering, or prompt injection) can study and bypass.

The HSR's controls are external. The gateway, kill switch, memory vaccine, and OS isolation
layer operate at layers the agent cannot influence:

```
Attack vector: "Bypass the approval check"
HSR response:  There is no approval check in agent code to bypass.
               The approval gate runs in the gateway, which the agent cannot modify.

Attack vector: "Inject instructions via retrieved memory"  
HSR response:  Memory content is scanned by the memory auditor before next session.
               The vaccine file loads first and establishes injection immunity.
               The gateway flags injection patterns before they reach the LLM.

Attack vector: "Read SSH keys via file tool"
HSR response:  HERMES_READ_SAFE_ROOT restricts reads to workspace.
               gVisor syscall filtering prevents OS-level file escapes.
               The vaccine explicitly blocks credential path reads.
```

---

## Layer Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  EXTERNAL INPUTS                                                      │
│  User · Telegram · Discord · Slack · WhatsApp · Signal · Email · MCP │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  LAYER 1: GATEWAY TAINT TRACKING                                      │
│  gateway/gateway.py + provider_adapters.py                            │
│  ─────────────────────────────────────────────────────────────────── │
│  · Tags all external-surface content before LLM injection             │
│  · Strips executable-like strings from tainted content               │
│  · Per-adapter sanitization for each platform                        │
│  AI SAFE²: P1.S-C05                                                  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  LAYER 2: MEMORY VACCINE (loads before all session memory)            │
│  core/hermes_memory_vaccine.md                                        │
│  ─────────────────────────────────────────────────────────────────── │
│  · Constitutional directives at highest memory priority               │
│  · Injection immunity patterns (8 directives)                        │
│  · Credential access blocks                                          │
│  · Identity anchor                                                   │
│  AI SAFE²: P1.S-C03                                                  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  LAYER 3: AI SAFE² GATEWAY (LLM reverse proxy)                        │
│  gateway/gateway.py                                                   │
│  ─────────────────────────────────────────────────────────────────── │
│  · PII filter (SSN, credit cards)                                    │
│  · Secrets filter (API keys, private keys, AWS/GCP/GitHub tokens)    │
│  · Injection pattern detection                                       │
│  · Request size enforcement                                          │
│  · Tool allowlist enforcement                                        │
│  · Kill switch check (every request)                                 │
│  · Immutable HMAC-chained audit log                                  │
│  AI SAFE²: P1.S-C02, P2.A-C05, P3.F-C05, P4.M-C01                  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  LAYER 4: HERMES AGENT CORE (sandboxed)                               │
│  nousresearch/hermes-agent + HSR environment overrides                │
│  ─────────────────────────────────────────────────────────────────── │
│  · HERMES_FORCE_APPROVAL=true (overrides Critical container default)  │
│  · HERMES_READ_SAFE_ROOT enforced (filesystem isolation)              │
│  · LLM credentials from Vault (not flat .env)                        │
│  · WECOM_ENABLED=false (CVE-2026-7396 mitigation)                    │
│  · HERMES_YOLO=false (no production YOLO mode)                       │
│  AI SAFE²: P1.S-C01, P1.S-C04, P3.F-C01, P3.F-C02                  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  LAYER 5: OS ISOLATION BOUNDARY                                       │
│  Docker + gVisor (runtime: runsc) + network policy                   │
│  ─────────────────────────────────────────────────────────────────── │
│  · Whole-process kernel isolation (gVisor)                           │
│  · Non-root user (1000:1000)                                         │
│  · no-new-privileges security option                                 │
│  · ALL capabilities dropped                                          │
│  · Internal-only network (no direct egress from hermes)              │
│  · Egress only via gateway network                                   │
│  AI SAFE²: P1.S-C01, P3.F-C03                                       │
└──────────────────────────────────────────────────────────────────────┘

Parallel monitoring layer (runs continuously, asynchronously):

┌──────────────────────────────────────────────────────────────────────┐
│  MEMORY AUDIT DAEMON                                                  │
│  monitoring/memory_auditor.py (60s interval)                         │
│  ─────────────────────────────────────────────────────────────────── │
│  · Scans SQLite memory stores for injection artifacts                │
│  · Scans markdown memory files                                       │
│  · Detects credential patterns written to memory                     │
│  · Auto-quarantine option for critical findings                      │
│  AI SAFE²: P4.M-C02                                                  │
├──────────────────────────────────────────────────────────────────────┤
│  ISHI SUPERVISOR                                                      │
│  supervisor/ + OPA policies                                          │
│  ─────────────────────────────────────────────────────────────────── │
│  · Kill switch enforcement                                           │
│  · Cron task governance (approval for unattended automation)         │
│  · Subagent scope inheritance enforcement                            │
│  · Behavioral baseline + 3σ anomaly detection                       │
│  AI SAFE²: P3.F-C05, P3.F-C06, P4.M-C06                            │
├──────────────────────────────────────────────────────────────────────┤
│  SKILL SCANNER (runs on install + hourly)                            │
│  gateway/scanner.py                                                  │
│  ─────────────────────────────────────────────────────────────────── │
│  · Scans skills for subprocess calls, eval, exec, credential paths   │
│  · Checks dependency pinning (git commit SHA requirement)            │
│  · Verifies skill provenance manifests                               │
│  AI SAFE²: P2.A-C01, P2.A-C02                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Credential Architecture

**Default Hermes (what we're replacing):**
```
.env → ANTHROPIC_API_KEY=sk-ant-... (static, long-lived, world-readable if permissions wrong)
```

**HSR credential architecture:**
```
HashiCorp Vault
  └── hermes/anthropic-key (dynamic, <1hr lifetime, audit logged)
       └── vault agent sidecar → injects ephemeral token into Hermes at runtime
            └── Gateway uses token to authenticate upstream
                └── Token rotated automatically before expiry
```

If Hermes is compromised and a credential is exfiltrated, the attacker has a token
that expires within the hour. Not a static key that works indefinitely.

---

## Subagent Governance

```
Operator request: "Research X and write a report"
        │
        ▼
Parent Hermes agent
  ├── Declares spawn: {task: "research X", tools: ["web_search"], scope: "read-only", duration: "30min"}
  ├── Logs spawn declaration to audit trail
  ├── Waits for operator confirmation if scope includes external network
  │
  └── Spawns Research Subagent
        ├── Receives ONLY web_search tool (not parent's full toolset)
        ├── Cannot access parent memory store
        ├── Cannot access Vault credentials
        ├── Returns structured results (not raw LLM output)
        │
        └── Parent validates subagent output (injection scan before use)
              └── Writes report with validated research content
```

---

## Multi-Platform Gateway Taint Flow

```
Telegram message arrives:
  "Hey Hermes, here's a doc to process: [malicious content with injection]"
         │
         ▼
gateway/platforms/telegram adapter
  · Source tagged: EXTERNAL-SOURCE:telegram
  · Injection scan on message body
  · Executable strings stripped
         │
         ▼
Memory vaccine directive 8:
  · All telegram input treated as untrusted
  · Content processed as data, not instructions
         │
         ▼
Memory auditor (next scan cycle):
  · If content was written to memory: injection pattern scan
  · Malicious instruction in stored memory: quarantine
```

---

## AI SAFE² Agent Classification

### ACT Capability Tier

Hermes Agent is classified as **ACT-3** (Autonomous Complex Task) under the AI SAFE² Agentic Capability Tier model:

| Tier | Definition | Hermes Classification |
|------|-----------|----------------------|
| ACT-1 | Single-step, no persistence, no tool use | No |
| ACT-2 | Multi-step, limited tools, no memory | No |
| **ACT-3** | **Multi-step, persistent memory, multi-tool, subagent delegation** | **Yes — Hermes v0.14.0** |
| ACT-4 | Autonomous swarm, recursive self-improvement, unsupervised deployment | Potential with skill system + cron |

**ACT-3 mandatory controls (enforced by HSR):**
- Persistent memory scan (memory_auditor.py — hourly)
- Subagent scope policy (subagent_scope.rego — spawn gate)
- HITL approval gates on all high-risk tools (tool_approval.rego)
- Kill switch with <5s activation (kill-switch.sh)
- Alignment monitoring via Love Equation (ishi_config.yaml)

> ACT-4 risk: Hermes' closed learning loop + community skill install + cron scheduler creates a potential ACT-3→ACT-4 drift path. HSR controls for this are: unsigned skill block, cron_governance.rego, subagent depth limit = 1.

---

### HEAR Doctrine (CP.10)

The **HEAR Doctrine** (Human Ethical Agent of Record — AI SAFE² Cross-Pillar Control CP.10) is implemented in HSR as follows:

The HEAR principle requires that a cryptographically accountable human remain on record as responsible for every consequential AI action. In HSR:

| HEAR Component | HSR Implementation |
|---------------|-------------------|
| Human designation | `ISHI_ALERT_EMAIL` in .env — the named operator of record |
| Ethical constraint | `core/SOUL.md` Love Equation alignment; vaccine directive integrity rules |
| Agent accountability | HMAC-chained audit log — every tool call signed and attributed |
| Record permanence | Append-only audit log; 365-day retention; SIEM forward |
| Fail-closed behavior | Ishi HITL timeout = deny; kill switch default = suspend |

The HEAR Doctrine is violated if: (a) no operator is named, (b) audit log is disabled, or (c) HITL timeout action is set to `allow`. HSR enforces all three.

---

## Compliance Architecture

| Control Domain | Framework | HSR Implementation |
|---|---|---|
| AI Supply Chain Security | CSA AICM v1.0 | Sovereign skills registry + scanner.py |
| Agent Identity Management | NIST AI RMF MAP-1 | NHI inventory via audit trail + Vault |
| Human in the Loop | NIST AI RMF GOV-5 | Ishi supervisor + approval gates |
| Prompt Injection Defense | OWASP LLM01 | Gateway filter + memory vaccine |
| Insecure Output Handling | OWASP LLM02 | Gateway output scan |
| Supply Chain Vulnerabilities | OWASP LLM06 | Scanner + dependency pinning |
| Agent Framework Threats | CSA MAESTRO L3 | Full HSR stack |
| Infrastructure Threats | CSA MAESTRO L4 | gVisor + network isolation |
| Credential Management | Zero Trust | Vault + ephemeral tokens |

---

*HSR Architecture Reference · Cyber Strategy Institute · AI SAFE² v3.0*
