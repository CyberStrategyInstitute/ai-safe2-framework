# AI SAFE² × SlowMist OpenClaw Security Practice Guide

## A Unified Security Architecture for High-Privilege Autonomous AI Agents

[![AI SAFE² Framework](https://img.shields.io/badge/AI%20SAFE%C2%B2-v2.1-blue)](https://github.com/CyberStrategyInstitute/ai-safe2-framework)
[![SlowMist Guide](https://img.shields.io/badge/SlowMist%20Guide-v2.7-green)](https://github.com/slowmist/openclaw-security-practice-guide)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What This Example Is

This example demonstrates how to combine the **SlowMist OpenClaw Security Practice Guide** (v2.7) with the **AI SAFE² Framework** to achieve full-stack security governance for a high-privilege OpenClaw deployment.

Neither framework alone is sufficient. Together, they cover every layer of the attack surface:

- **SlowMist** provides the agent-facing runtime safety harness: behavioral rules encoded into the agent's own reasoning layer, supply-chain audit protocols, in-action execution controls, and a rigorous nightly 13-metric audit structure.
- **AI SAFE²** provides the external governance control plane: the Memory Vaccine, Vulnerability Scanner, and Control Gateway tools, plus organizational controls (cross-deployment inventory, anomaly detection, incident playbooks, adversarial drills) that SlowMist explicitly does not cover.

This repository provides:

| Asset | Purpose |
|---|---|
| [`safe2-for-slowmist-overlay.md`](./safe2-for-slowmist-overlay.md) | One-pager mapping every SlowMist control into the five AI SAFE² pillars, with tool placement diagram |
| [`control-mapping-table.md`](./control-mapping-table.md) | Full cross-reference table: SlowMist control → AI SAFE² pillar → tool(s) → gap analysis |
| [`deployment-checklist.md`](./deployment-checklist.md) | Step-by-step deployment order for adding AI SAFE² tools to an existing SlowMist deployment |
| [`threat-model.md`](./threat-model.md) | Combined threat model: SlowMist's defined scope + AI SAFE²'s extended blast radius |
| [`red-team-schedule.md`](./red-team-schedule.md) | Recurring adversarial exercise schedule built on SlowMist's Validation Guide curriculum |
| Reference Section Below | Curated references, research papers, and further reading |

---

## Background: Why These Two Frameworks Belong Together

### The Problem

OpenClaw is an autonomous AI agent framework with root-level terminal access. It installs and runs Skills, manages files, calls external APIs, and executes multi-step workflows without synchronous human approval. It is not a chatbot. It is an always-on execution engine.

Independent academic research testing OpenClaw across 47 adversarial scenarios found a baseline native defense rate of just 17% against sandbox escape attacks. This is not a criticism of OpenClaw — it is a structural property of any LLM-based agent that relies on the model's own safety training as its primary control. External enforcement is required.

### The Gap Each Framework Leaves

**SlowMist (standalone):**
- ✅ Excellent: agent-facing behavioral rules, supply chain intake, per-box audit, disaster recovery
- ❌ Weak: no cross-deployment visibility, no real-time gateway enforcement, no cross-agent anomaly detection, no organizational training cadence, 24-hour detection latency for hash baseline drift

**AI SAFE² (standalone):**
- ✅ Excellent: external gateway enforcement, organizational governance, multi-deployment inventory, adversarial exercise cadence
- ❌ Weak: does not prescribe a specific behavioral taxonomy for the agent's cognitive layer, no nightly 13-metric audit structure, no skill supply-chain intake protocol

**Together:**
- ✅ Full-stack coverage from agent cognition → runtime execution → API gateway → organizational governance

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      UNIFIED SECURITY ARCHITECTURE                      │
│                                                                         │
│   ORGANIZATIONAL LAYER (AI SAFE² Pillars 2, 4, 5)                       │
│   • Cross-deployment automation registry                                │
│   • Fleet-wide behavioral anomaly detection                             │
│   • Quarterly red-team exercises (SlowMist curriculum)                  │
│   • Annual threat model review                                          │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  GATEWAY LAYER — Control Gateway (AI SAFE² Pillar 4)            │   │
│   │  • Sits between OpenClaw ↔ LLM API                              │   │
│   │  • Real-time risk scoring, prompt injection blocking            │   │
│   │  • High-risk tool denial, immutable API-layer audit logs        │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  AGENT HOST LAYER — SlowMist Defense Matrix                     │   │
│   │                                                                 │   │
│   │  Pre-action: Red/Yellow Lines + Skill Audit                     │   │
│   │     └── Memory Vaccine (AI SAFE² Pillar 1) ◀── cognitive layer │   │
│   │                                                                 │   │
│   │  In-action: Permission Narrowing + Hash Baseline + Logs         │   │
│   │     └── Gateway enforcement continues here ◀────────────────── │   │
│   │                                                                 │   │
│   │  Post-action: Nightly 13-Metric Audit + Brain Backup            │   │
│   │     └── Vulnerability Scanner (AI SAFE² Pillar 2) ◀── here     │   │
│   └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- OpenClaw deployed and running
- SlowMist OpenClaw Security Practice Guide v2.7 applied (or in progress)
- Python 3.8+ (for Vulnerability Scanner)
- Node.js / Docker (for Control Gateway, see gateway/ directory)

### Step 1: Deploy the Memory Vaccine

Add `openclaw_memory.md` to OpenClaw's memory bank. This is the cognitive-layer enforcement that complements SlowMist's behavioral red/yellow lines.

```bash
# From the AI SAFE² examples/openclaw directory
cp openclaw_memory.md ~/.openclaw/workspace/
# Then in OpenClaw chat: "Please load and prioritize the security context in openclaw_memory.md"
```

### Step 2: Run the Vulnerability Scanner (Baseline)

Establish your pre-deployment security baseline before activating any new skills.

```bash
wget https://raw.githubusercontent.com/CyberStrategyInstitute/ai-safe2-framework/main/examples/openclaw/scanner.py
python3 scanner.py --target ~/.openclaw
```

Review the 0–100 risk score and remediate CRITICAL findings before proceeding.

### Step 3: Deploy the Control Gateway

```bash
# From the AI SAFE² examples/openclaw/gateway directory
# See gateway/README.md for full configuration options
```

Point OpenClaw's LLM API calls through the gateway. The gateway handles all subsequent requests with real-time enforcement.

### Step 4: Integrate with SlowMist Nightly Audit

Add the Scanner to SlowMist's existing nightly cron:

```bash
# Append to your existing nightly-security-audit.sh, or add as a separate cron:
# 0 3 * * * python3 /path/to/scanner.py --target ~/.openclaw >> /tmp/openclaw/security-reports/scanner-$(date +%Y-%m-%d).txt
```

Route both SlowMist audit reports and Scanner output to your centralized log aggregator for cross-deployment visibility.

### Step 5: Schedule Red-Team Exercises

Use the `red-team-schedule.md` in this directory to plan recurring adversarial exercises using SlowMist's Validation Guide as your test curriculum.

---

## The Five Pillars — Control Mapping Summary

| AI SAFE² Pillar | Primary SlowMist Controls | AI SAFE² Tool | Key Gap Closed |
|---|---|---|---|
| **Sanitize & Isolate** | Red/yellow lines, skill installation audit, dedicated VM | Memory Vaccine | Persistent cognitive-layer enforcement; memory poisoning prevention |
| **Audit & Inventory** | 13-metric nightly audit, hash baseline, skill baseline | Vulnerability Scanner | Secret exposure, network binding checks, 0–100 risk score |
| **Fail-Safe & Recovery** | Human confirmation gates, brain backup, state/key separation | Gateway circuit-breakers | Automated pre-emptive halts; no 24h detection gap |
| **Engage & Monitor** | Pre-flight checks, process/network audit, yellow-line counts | Control Gateway | Real-time API-layer enforcement; cross-agent anomaly correlation |
| **Evolve & Educate** | Red-team validation guide, agent-native deployment, threat model docs | Recurring drill schedule | Codified exercise cadence; annual threat model refresh |

For the complete control-by-control mapping, see [`safe2-for-slowmist-overlay.md`](./safe2-for-slowmist-overlay.md).

---

## Repository Contents

```
examples/slowmist-overlay/
├── README.md                        ← You are here
├── safe2-for-slowmist-overlay.md    ← One-pager: full pillar mapping + tool placement diagram
├── control-mapping-table.md         ← Complete cross-reference table
├── deployment-checklist.md          ← Step-by-step deployment order
├── threat-model.md                  ← Combined threat model
├── red-team-schedule.md             ← Recurring adversarial exercise schedule
└── resources.md                     ← Research papers, references, further reading
```

---

## Contributing

This overlay is maintained by the Cyber Strategy Institute. Contributions that improve the mapping, add new SlowMist controls as they are released, or document deployment patterns from the community are welcome.

Please open an issue before submitting a PR for substantive changes to the architecture or pillar mappings.

---

## References

- [SlowMist OpenClaw Security Practice Guide v2.7](https://github.com/slowmist/openclaw-security-practice-guide)
- [AI SAFE² Framework v2.1](https://github.com/CyberStrategyInstitute/ai-safe2-framework)
- [OpenClaw](https://github.com/openclaw/openclaw)
- [SlowMist Security Validation & Red Teaming Guide](https://github.com/slowmist/openclaw-security-practice-guide/blob/main/docs/Validation-Guide-zh.md)
- [Don't Let the Claw Grip Your Hand: Security Analysis of OpenClaw](https://arxiv.org/html/2603.10387) — Empirical study: 47 adversarial scenarios, 17% baseline defense rate
- [OpenClaw Security Survival Guide — Penligent](https://www.penligent.ai/hackinglabs/openclaw-security-survival-guide-from-fun-local-agent-to-defensible-runtime/)
- [AI SAFE² OpenClaw Security Analysis — Cyber Strategy Institute](https://cyberstrategyinstitute.com/openclaw-security-upgrades-2026-2-13/)

---

## License

This overlay documentation is licensed under CC-BY-SA 4.0, consistent with the AI SAFE² Framework methodology license. Code components follow MIT. See the root-level LICENSE files for details.

---

*"If governance is not enforced at runtime, it is not governance. It is forensics."*
*— Cyber Strategy Institute*
