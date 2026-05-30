# Hermes Sovereign Runtime (HSR)
### AI SAFE² v3.0 Defense Package for NousResearch/hermes-agent

**Cyber Strategy Institute** · MIT License · Framework: AI SAFE² v3.0

---

> **Hermes Agent is the most capable open-source autonomous agent runtime available today.**
> It is also running on your workstation with shell access, a full credential store, persistent memory that learns from everything it reads, and zero enforcement boundaries by default.
>
> This package is the enforcement boundary.

---

## Why This Exists

Hermes Agent v0.14.0 ships with four Critical security findings in its default configuration — none of them assigned CVE identifiers yet, all of them exploitable today:

| Finding | Severity | Status |
|---|---|---|
| Unrestricted shell execution via `tools/terminal_tool.py` | **Critical** | No fix in default config |
| Container deployment disables ALL approval checks | **Critical** | Architectural default |
| Persistent skill injection to `~/.hermes/skills/` | **Critical** | No signing enforcement |
| Indirect prompt injection via memory retrieval | **Critical** | No EDR detection possible |

The third-party April 2026 audit of v0.8.0 found four Critical + nine High findings across 812 Python files. Three CVEs have been disclosed as of May 2026. The architectural risks are larger than the CVE list suggests — and they're the same class of risk that gave OpenClaw nine CVEs in four days during March 2026.

**This package does not ask Hermes to be more careful. It enforces boundaries the agent cannot see or influence.**

---

## What This Package Delivers

```
User Request
    │
    ▼
┌─────────────────────────────────────────┐
│         MEMORY VACCINE                  │  ← Constitutional directives injected
│   hermes_memory_vaccine.md              │    at highest memory priority
└─────────────────┬───────────────────────┘
                  │
    ▼
┌─────────────────────────────────────────┐
│         AI SAFE² GATEWAY                │  ← Reverse proxy: PII filter, secrets
│   gateway/gateway.py                    │    filter, tool allowlist, audit log
└─────────────────┬───────────────────────┘
                  │
    ▼
┌─────────────────────────────────────────┐
│         HERMES AGENT CORE               │  ← gVisor-isolated, no new privileges,
│   nousresearch/hermes-agent             │    workspace-sandboxed, Vault-credentialed
└─────────────────┬───────────────────────┘
                  │
    ▼
┌─────────────────────────────────────────┐
│         ISHI SUPERVISOR                 │  ← Kill switch, approval gate, anomaly
│   supervisor/                           │    detection, cron governance
└─────────────────────────────────────────┘
```

**Five AI SAFE² pillars. One deployable stack. 15-minute install.**

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/CyberStrategyInstitute/ai-safe2-framework
cd ai-safe2-framework/examples/hermes-sovereign-runtime

# 2. Copy and configure environment
cp .env.example .env
# Edit .env — minimum: set your LLM API key

# 3. Run pre-flight check
bash scripts/pre-flight-check.sh

# 4. Deploy sovereign stack
docker compose up -d

# 5. Verify
bash validation/pass1_static.sh && bash validation/pass2_runtime.sh
```

**That's it.** Hermes now runs behind the AI SAFE² gateway with memory vaccination, approval enforcement, credential isolation, and a live kill switch.

---

## Package Structure

```
hermes-sovereign-runtime/
│
├── README.md                          # You are here
├── SECURITY.md                        # Vulnerability disclosure policy
├── docker-compose.yml                 # Sovereign runtime stack
├── .env.example                       # Configuration template
│
├── core/                              # Governance files — drop into ~/.hermes/memories/
│   ├── README.md
│   ├── hermes_memory_vaccine.md       # ★ MOST CRITICAL — load first
│   ├── IDENTITY.md                    # Agent identity anchor
│   ├── SOUL.md                        # Alignment constitution (Love Equation)
│   ├── TOOLS.md                       # Tool configuration standard
│   ├── SUBAGENT-POLICY.md             # Subagent delegation governance
│   └── HEARTBEAT.md                   # Scheduled health check protocol
│
├── gateway/                           # AI SAFE² LLM enforcement proxy
│   ├── README.md
│   ├── gateway.py                     # Flask reverse proxy with control plane
│   ├── scanner.py                     # Skill/plugin/memory anomaly scanner
│   ├── provider_adapters.py           # Multi-provider adapter (Anthropic/OpenAI/Gemini/Ollama)
│   ├── config.yaml                    # Thresholds, allowlists, provider config
│   └── start.sh                       # Pre-flight validator + launcher
│
├── supervisor/                        # Ishi supervisor — kill switch + policy
│   ├── README.md
│   ├── ishi_config.yaml               # Supervisor configuration
│   └── policies/
│       ├── tool_approval.rego         # OPA: high-risk tool gate
│       ├── cron_governance.rego       # OPA: unattended automation approval
│       └── subagent_scope.rego        # OPA: capability inheritance limits
│
├── monitoring/                        # Observability stack
│   ├── README.md
│   ├── memory_auditor.py              # Memory store anomaly detection daemon
│   ├── prometheus.yml                 # Metrics scrape config
│   ├── alerts.yaml                    # Grafana alert rules
│   └── dashboards/
│       └── hermes_sovereign.json      # Pre-built Grafana dashboard
│
├── skills-registry/                   # Sovereign skill approval pipeline
│   ├── README.md
│   ├── verify_skill.sh                # Code signing + behavior analysis gate
│   ├── skill_manifest_template.yaml   # Provenance record template
│   └── approved/                      # Signed, approved skill store
│
├── scripts/                           # Operational runbooks as code
│   ├── README.md
│   ├── install.sh                     # One-command install
│   ├── pre-flight-check.sh            # 25-point deployment validation
│   ├── kill-switch.sh                 # Immediate execution suspension
│   ├── rotate-credentials.sh          # Emergency credential rotation
│   └── audit-report.sh               # Compliance evidence generator
│
├── validation/                        # 5-pass QA/adversarial test suite
│   ├── README.md
│   ├── pass1_static.sh                # Static configuration review
│   ├── pass2_runtime.sh               # Runtime behavior validation
│   ├── pass3_adversarial.py           # Red team: injection, traversal, exfil
│   ├── pass4_compliance.sh            # Compliance mapping verification
│   └── pass5_readiness.sh             # Operational readiness gate
│
└── docs/
    ├── ARCHITECTURE.md                # Full HSR architecture reference
    ├── THREAT-MODEL.md                # Hermes-specific threat model
    ├── COMPLIANCE-MAPPING.md          # NIST AI RMF / CSA AICM / MAESTRO
    ├── INCIDENT-RESPONSE.md           # Credential rotation, memory quarantine runbooks
    └── MIGRATION.md                   # Upgrading from unprotected Hermes
```

---

## What Each Layer Defends

| Layer | What It Stops | AI SAFE² Pillar |
|---|---|---|
| **Memory Vaccine** | Prompt injection persisting across sessions; identity replacement attacks | P1 Sanitize & Isolate |
| **AI SAFE² Gateway** | PII/credentials in LLM context; over-limit requests; unauthorized tools | P1 + P2 |
| **Skill Scanner** | Malicious community skills; supply chain substitution; unsigned imports | P2 Audit & Inventory |
| **Approval Gate Override** | Container deployment bypassing all approval checks (Critical default bug) | P3 Fail-Safe |
| **gVisor Isolation** | Shell escape; filesystem traversal; out-of-scope file reads | P1 + P3 |
| **HashiCorp Vault** | Long-lived credentials; flat .env compromise; key sprawl | P1 + P2 |
| **Ishi Supervisor** | YOLO-mode production use; unapproved cron automation; runaway subagents | P3 + P4 |
| **Memory Auditor** | Indirect prompt injection via retrieved memory (invisible to EDR) | P4 Engage & Monitor |
| **Kill Switch** | Immediate execution halt on anomaly; zero-latency response | P3 Fail-Safe |
| **Sovereign Skills Registry** | Community hub skills as execution vectors; malicious skill persistence | P2 + P5 |

---

## The Core Threat This Solves

Standard EDR tools cannot detect the most dangerous Hermes attack vector:

**Indirect prompt injection through memory retrieval.**

When Hermes reads a malicious document, email, or web page, attacker-controlled content gets written to its SQLite memory store. In a future session, that content is retrieved and injected into the model's context window — carrying adversarial instructions the model executes as legitimate user commands.

No file write. No anomalous process spawn. No network signature. Nothing for EDR to catch.

The HSR memory vaccine, taint-tracking middleware, and memory audit daemon are the only controls that operate at the semantic layer where this attack executes.

---

## Threat Surface Comparison

| Hermes Default | With HSR |
|---|---|
| File reads: any path the process can access | Restricted to `HERMES_READ_SAFE_ROOT` |
| Shell execution: `bash -c` with regex-only filtering | OS-level isolation (gVisor) + approval gate |
| Container deployment: zero approval checks | `HERMES_FORCE_APPROVAL=true` enforced |
| Skills: install from community hub, no review | Sovereign registry: code review + signing required |
| Credentials: flat `.env` file | HashiCorp Vault ephemeral tokens (<1hr lifetime) |
| Memory: persists all retrieved content | Vaccine + taint-tracking + hourly audit scan |
| Monitoring: none | Semantic anomaly detection + SIEM forwarding |
| Kill switch: none | Ishi supervisor, sub-second response |
| Subagents: inherit parent capabilities | Explicit scope declaration required |

---

## Compliance Alignment

This package maps controls to:

- **NIST AI RMF** — Govern / Map / Measure / Manage functions
- **CSA AICM v1.0** — AI Supply Chain Security, Agent Lifecycle Management
- **CSA MAESTRO** — Layer 3 (Agent Framework) + Layer 4 (Infrastructure) threat chains
- **OWASP LLM Top 10** — LLM01 (Prompt Injection), LLM02 (Insecure Output), LLM06 (Supply Chain)
- **Zero Trust** — Never trust, always verify credential access

See [`docs/COMPLIANCE-MAPPING.md`](docs/COMPLIANCE-MAPPING.md) for the full control-to-framework crosswalk.

---

## Who This Is For

| Persona | Primary Risk | HSR Value |
|---|---|---|
| **Individual developers** | Credential exfiltration via prompt injection | Gateway + memory vaccine in 15 min |
| **Enterprise teams** | Unaudited agent activity, compliance gaps | Immutable audit trail + SIEM integration |
| **DIB / Government** | Supply chain compromise, A2A trust | Sovereign skills registry + NEXUS-A2A attestation |
| **MSPs / consultants** | Client liability from misconfigured agents | Pre-flight checklist + 5-pass QA |

---

## Relationship to OpenClaw Sovereign Runtime

This package directly extends the pattern established by the [OpenClaw Sovereign Runtime](../openclaw/) in the AI SAFE² framework:

| OpenClaw Component | HSR Equivalent | What's New |
|---|---|---|
| `openclaw_memory.md` vaccine | `core/hermes_memory_vaccine.md` | Extended for self-improving skill loop |
| `scanner.py` | `gateway/scanner.py` | Extended for Skills Hub + 7 terminal backends |
| `gateway.py` | `gateway/gateway.py` | Per-adapter taint-tracking for 6+ platform adapters |
| Ishi supervisor | `supervisor/` | Subagent delegation governance + scope inheritance |
| Single-provider proxy | Multi-provider adapter | 200+ models via OpenRouter, NIM, HuggingFace |

Hermes Agent's self-improving skill loop and multi-platform gateway require controls OpenClaw never needed. HSR adds them.

---

## Built On

- **AI SAFE² Framework v3.0** — Cyber Strategy Institute
- **Hermes Agent** — NousResearch (MIT License)
- **Love Equation alignment dynamics** — Brian Roemmele
- **NEXUS-A2A v0.2** — Non-repudiable agent-to-agent attestation
- **CSA MAESTRO** — Multi-agent threat taxonomy
- **HashiCorp Vault** — Ephemeral credential management
- **gVisor** — Kernel-level process isolation

---

## License

MIT (code) + CC-BY-SA 4.0 (documentation)

**Cyber Strategy Institute** | AI SAFE² Framework
[GitHub](https://github.com/CyberStrategyInstitute/ai-safe2-framework) · [ai-safe2.com](https://ai-safe2.com)

*Autonomous AI is only valuable when it is governable.*
