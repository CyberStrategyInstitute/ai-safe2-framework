# AI SAFE² Sovereign Compliance Suite for Antigravity 2.0

This repository provides a concrete, runnable reference implementation of the **AI SAFE² Framework v3.0** tailored specifically to secure and govern the **Antigravity 2.0 Agentic Platform**. 

It adopts the **Two-Layer Agent Security Model**:
1. **Internal Alignment & Policy Layer (`core/`)**: Mappings loaded directly into the agent's context window that establish its identity, role limits, values, and allowed tools.
2. **External Inspection & Enforcement Layer (`enforcement/`)**: Native scripts that run outside the LLM context, intercepting file modifications, shell executions, and network requests to block attacks before they escape the container.

---

## 🏗️ Repository Architecture & Control Mapping

The code suite is structured to map directly to the 5 Operational Pillars of the **AI SAFE² Standard**:

```
ai_safe2_antigravity/
├── core/                         # INTERNAL GOVERNANCE LAYER (Pillar 1 / CP.4)
│   ├── IDENTITY.md               # CP.4 Non-Human Identity Registered Profile
│   ├── SOUL.md                   # S1.4 Behavioral Containment & Hard Limits
│   ├── GOVERNANCE.md             # Pillar 1 Context Isolation Architecture
│   ├── TOOLS.md                  # S1.3 Capability & Tool Authorization Whitelist
│   ├── USER.md                   # P4.HITL Human-In-The-Loop trust controls
│   └── MEMORY.md                 # S1.5 Memory Governance & State Hygiene
├── enforcement/                  # EXTERNAL ENFORCEMENT LAYER
│   ├── safe_gateway.js           # Pillar 1 Secret Scanner & Pillar 4 Gateway
│   ├── circuit_breaker.js        # Pillar 3 Swarm Abort & Recursion Breaker
│   └── audit_logger.js           # Pillar 2 Audit Verification Ledger
└── smoke_test.js                 # Verification test harness
```

---

## 🚀 Quick Start & Verification

We have implemented an automated test harness to prove that these controls effectively intercept and containerize agentic threats (e.g. Prompt Injections, Path Traversals, Secret Exfiltration, and Runaway Swarm Loops).

### 1. Run the Security Controls Test Suite
Run the test harness in your terminal using the native, embedded Electron-node engine (`agy-node`):

```powershell
agy-node smoke_test.js
```

### 2. Verify Output & Reports
Once executed, the test suit will run 5 high-fidelity mock attacks against the sandbox gateway, log all containment events in `enforcement/audit.log`, and automatically compile a formal, compliance report:

- Inspection Log: `enforcement/audit.log`
- Compliance GRC Ledger: `enforcement/ai_safe2_compliance_report.md`

---

## 🛡️ Key Controls Implemented

### Pillar 1: Sanitize & Isolate
- **Secret Scanning**: Scans all write streams using regex signatures for AWS keys, Stripe tokens, and GitHub credentials, blocking credential leaks to disk (`safe_gateway.js:L97`).
- **Prompt Isolation**: Cleanses raw string streams of dynamic system prompt update attempts (`safe_gateway.js:L42`).
- **Path Verification**: Limits all file writes and edits to safe workspace paths.

### Pillar 2: Audit & Inventory
- **Unified Transaction Log**: Saves a tamper-evident record of all sandbox decisions in standard UTC format (`safe_gateway.js:L30`).
- **Compliance Auto-Reporter**: Aggregates alerts and outputs certified compliance summaries (`audit_logger.js`).

### Pillar 3: Fail-Safe & Recovery
- **Swarm Circuit Breaker**: Counts rapid identical tool calls to intercept loop drift or fork bombs, tripping execution bounds and performing rollback calls (`circuit_breaker.js`).
- **Multi-Command Injection Block**: Rejects multi-statement shell commands chained via `;` or `&&` (`safe_gateway.js:L81`).
