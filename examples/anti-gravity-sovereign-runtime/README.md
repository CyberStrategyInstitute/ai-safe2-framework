# 🛡️ AI SAFE² Sovereign Compliance Suite for Antigravity 2.0

> **Prevention over detection. Engineering over policy. Milliseconds beat committees.**

A runnable reference implementation of the **AI SAFE² Framework v3.0** — designed to govern and harden the **Antigravity 2.0 Agentic Platform** against prompt injection, exfiltration, privilege escalation, and runaway execution.

---

## What This Is

This suite gives your Antigravity workspace a **three-layer security architecture**. The layers are distinct — understand which one is active and why:

```
┌──────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — PLATFORM ENFORCEMENT                                      │
│  Antigravity's own system prompts, tool safety, and platform rules.  │
│  Pre-loaded before any session. NOT part of this repo.               │
└─────────────────────────────────────────┬────────────────────────────┘
                                          │ augmented by
┌─────────────────────────────────────────▼────────────────────────────┐
│  LAYER 2 — GOVERNANCE INJECTION (core/ + plugin)                     │
│  AI SAFE² identity lock, hard limits, tool authorization, HITL.      │
│                                                                       │
│  ⚠️ core/*.md files are PROJECT files — NOT auto-loaded by default.  │
│  Activation requires ONE of:                                          │
│    A) governance-enforcer plugin  (recommended)                       │
│    B) system_prompt config injection                                  │
│    C) .agent/rules/ workspace files  (redundant layer)               │
│                                                                       │
│  Without wiring, core/ is documentation. With wiring, it's law.      │
└─────────────────────────────────────────┬────────────────────────────┘
                                          │ enforced by
┌─────────────────────────────────────────▼────────────────────────────┐
│  LAYER 3 — EXTERNAL ENFORCEMENT (enforcement/)                        │
│  Runs OUTSIDE the LLM. Intercepts tool calls before execution.       │
│  Gateway → Circuit Breaker → Audit Logger                             │
│  Fail-closed: if the gateway errors, the action is DENIED.           │
│  Active regardless of whether Layer 2 governance files are loaded.   │
└──────────────────────────────────────────────────────────────────────┘
```

**The critical distinction:** Layer 3 enforces controls whether or not the agent has read SOUL.md. An LLM session that never loaded the governance files still gets its tool calls blocked by the gateway. Layer 2 adds defense-in-depth by aligning the agent's behavior before it even attempts a tool call.

---

## 30-Second Quick Start

### Windows (Antigravity Native)

```powershell
# 1-click deploy and verify
.\deploy.ps1
```

### Node.js (any platform)

```bash
# Run full test suite (13 adversarial scenarios)
node smoke_test.js

# JSON output (for CI/CD)
node smoke_test.js --json

# Run specific tier only
node smoke_test.js --tier 2
```

**Expected output:**
```
🛡️  AEGIS-ANTIGRAVITY  //  AI SAFE² SOVEREIGN RUNTIME TEST SUITE
   13-Scenario Adversarial Verification Harness

── Tier 1: Core Controls ──────────────────────────────────────

[PASS] [T1] [T1.01] Indirect Prompt Injection Filtering
         → Injection neutralized. Matches: 1

[PASS] [T1] [T1.02] Outbound Exfiltration — Non-Whitelisted Domain
         → Blocked correctly.
...

✅ Passed: 13/13
🛡️  STATUS: SECURE BASELINE VERIFIED.
```

---

## Repository Structure

```
anti-gravity-sovereign-runtime/
│
├── core/                          # GOVERNANCE DOCUMENTS (need wiring — see below)
│   ├── IDENTITY.md                # CP.4: NHI Registration Profile
│   ├── SOUL.md                    # S1.4: Behavioral Boundaries & Hard Limits
│   ├── GOVERNANCE.md              # P1: Context Isolation Architecture
│   ├── TOOLS.md                   # S1.3: Tool Authorization Whitelist
│   ├── USER.md                    # P4.HITL: Human-in-the-Loop Controls
│   └── MEMORY.md                  # S1.5: Memory Governance & State Hygiene
│
├── plugins/                       # OPTION 1: NATIVE PLUGIN (recommended)
│   └── governance-enforcer/
│       ├── plugin.json            # Plugin manifest (autoLoad: true)
│       ├── prompts/
│       │   └── system-governance.md  # System prompt loaded every session
│       └── skills/governance/
│           └── SKILL.md           # Session behavior rules
│
├── .agent/rules/                  # OPTION 3 COMPLEMENT: workspace auto-load rules
│   ├── governance-soul.md         # Hard limits + escalation (mirrors SOUL.md)
│   ├── governance-identity-tools.md  # Identity + tool auth (mirrors IDENTITY+TOOLS)
│   └── governance-memory-context.md  # Memory + context isolation (mirrors MEMORY)
│
├── config/                        # INSTALL SCRIPTS
│   ├── governance-system-prompt.md        # Canonical governance prompt text
│   ├── install-option1-plugin.ps1         # Installs governance-enforcer plugin
│   └── install-option3-system-prompt.ps1  # Injects into global system_prompt config
│
├── controls/                      # MACHINE-READABLE POLICY MANIFEST
│   └── policy.yaml                # Control registry with maturity + loaded_at_runtime
│
├── enforcement/                   # EXTERNAL ENFORCEMENT LAYER (active regardless)
│   ├── safe_gateway.js            # P1+P4: Input sanitizer, URL/cmd/path/secret gate
│   ├── circuit_breaker.js         # P3: Loop detector, subagent + memory guardian
│   └── audit_logger.js            # P2: Evidence-grade audit + JSON + SARIF output
│
├── tests/
│   └── adversarial/               # Standalone adversarial test scripts
│
├── reports/                       # Generated outputs (gitignored)
│   ├── ai_safe2_compliance_report.md
│   ├── ai_safe2_evidence.json     # SHA-256 hashed evidence ledger
│   └── ai_safe2_results.sarif     # CI/CD security tool integration
│
├── scripts/
│   ├── run-all-verifications.sh   # Unified profile-based runner
│   └── verify-setup.sh            # Repo hygiene bootstrap verifier
│
├── smoke_test.js                  # 13-scenario adversarial verification harness
├── deploy.ps1                     # 1-click Windows deployer
├── INTEGRATION-GUIDE.md           # Step-by-step wiring guide for Antigravity
└── README.md                      # You are here
```

---

## Control Coverage

### What Is Enforced (with evidence)

| Control ID | Name | Tier | Tests |
|:---|:---|:---:|:---:|
| `P1.INJECT` | Indirect Prompt Injection Defense | T1 | T1.01 |
| `P1.SECRET` | Cleartext Credential Leak Prevention | T1 | T1.04 |
| `P1.PATH` | Path Traversal & Symlink Escape | T2 | T2.01, T2.02, T2.03 |
| `P1.DOMAIN` | Domain Allowlist + SSRF + Private IP | T1/T2 | T1.02, T2.04–T2.07 |
| `P1.CMD` | Command Allowlist & Chain Injection Block | T1/T3 | T1.03, T3.01 |
| `P1.SUBAGENT` | Subagent Privilege Boundary | T3 | T3.02, T3.03 |
| `P1.MEMORY` | Memory Poisoning Prevention | T3 | T3.04 |
| `A2.2` | Structured Audit Trail & Evidence | All | All |
| `F3.2` | Recursion Depth Circuit Breaker | T1 | T1.05 |
| `CP.4` | NHI Identity Registration | — | File present |
| `S1.3` | Tool Authorization Whitelist | T1 | T1.03 |
| `S1.4` | Behavioral Containment (SOUL) | — | File present |
| `S1.5` | Memory Governance | T3 | T3.04 |

### Known Gaps (Not Implemented — Be Honest)

| Gap | Severity | Description |
|:---|:---:|:---|
| `GAP-01` | Medium | Rollback is a stub — production wiring required |
| `GAP-02` | Medium | IDENTITY.md has no cryptographic signature |
| `GAP-03` | Low | Audit log is append-only, not cryptographically chained |
| `GAP-04` | Low | HITL notification is log-only, no real-time webhook |
| `GAP-05` | Medium | Subagent identity signing is documented, not enforced |

Full gap list in `controls/policy.yaml`.

---

## Control Maturity Model

Use these levels to communicate honestly about implementation depth:

| Level | Description | Example |
|:---|:---|:---|
| **Attested** | CI-verified with evidence hash | _(Roadmap)_ |
| **Tested** | Automated test with pass/fail result | `P1.PATH`, `P1.INJECT` |
| **Implemented** | Code covers the control, no formal test | `CP.4`, `S1.4` |
| **Documented** | Policy defined, not yet in code | `F3.4` (rollback) |
| **Planned** | Roadmap item | Cryptographic log chaining |

---

## Integration Guide for Antigravity Users

### Step 1: Deploy the Governance Layer

Copy `core/` into your Antigravity workspace. These files must be loaded at the **absolute start** of every session context window.

In Antigravity, open your workspace settings and set session initialization to load:

```
core/IDENTITY.md
core/SOUL.md
core/GOVERNANCE.md
core/TOOLS.md
core/USER.md
core/MEMORY.md
```

**Order matters.** IDENTITY → SOUL → GOVERNANCE → TOOLS → USER → MEMORY.

### Step 2: Wire the Enforcement Gateway

Integrate `safe_gateway.js` as an interceptor for every tool call:

```javascript
const SafeGateway = require('./enforcement/safe_gateway');

const gateway = new SafeGateway({
  workspaceRoot: '/path/to/your/workspace',
  whitelistedDomains: ['your-api.company.com', 'github.com'],
  whitelistedCommandPrefixes: ['npm', 'node', 'git'],
});

// Before any tool executes:
function executeToolAction(action, payload) {
  const check = gateway.verifyAction(action, payload);
  if (!check.authorized) {
    throw new Error(`Blocked: ${check.message}`);
  }
  // ... proceed with tool execution
}
```

### Step 3: Wire the Circuit Breaker

```javascript
const CircuitBreaker = require('./enforcement/circuit_breaker');

const breaker = new CircuitBreaker(
  5,      // max identical calls
  5000,   // within 5 seconds
);

// Before spawning a subagent:
const spawnCheck = breaker.validateSubagentSpawn({
  agentName:   'research-agent',
  mode:        'sandboxed',
  permissions: ['read'],
});
if (!spawnCheck.authorized) throw new Error(spawnCheck.reason);

// Register all tool calls:
function onToolCall(toolName, args) {
  const loopCheck = breaker.registerCall(toolName, args);
  if (loopCheck.tripped) throw new Error(loopCheck.reason);
}

// Before any memory write:
function saveToMemory(content) {
  const memCheck = breaker.validateMemoryWrite(content);
  if (!memCheck.safe) throw new Error(memCheck.reason);
  // ... persist
}
```

### Step 4: Run Verification

```bash
node smoke_test.js
```

All 13 tests must pass before production use. If any fail, check `enforcement/audit.log` for the blocking control and review `controls/policy.yaml` for the gap.

### Step 5: Review Outputs

| Output | Location | Purpose |
|:---|:---|:---|
| Audit Log | `enforcement/audit.log` | Structured JSON event stream |
| Compliance Report | `reports/ai_safe2_compliance_report.md` | Human-readable summary |
| Evidence Ledger | `reports/ai_safe2_evidence.json` | SHA-256 verified control evidence |
| SARIF Report | `reports/ai_safe2_results.sarif` | GitHub/CodeQL/CI integration |

---

## Customization

### Add Domains to the Allowlist

```javascript
const gateway = new SafeGateway({
  whitelistedDomains: [
    'api.openai.com',
    'your-internal-api.company.com',
    'github.com',
  ],
});
```

### Adjust Circuit Breaker Sensitivity

```javascript
// More sensitive (tighter recursion guard)
const breaker = new CircuitBreaker(3, 2000);

// More permissive (batch processing workloads)
const breaker = new CircuitBreaker(20, 30000);
```

### Extend Secret Detection

Add patterns to `secretPatterns` in `safe_gateway.js`:

```javascript
this.secretPatterns['GCP Service Account Key'] = /"type":\s*"service_account"/g;
this.secretPatterns['Azure SAS Token'] = /sig=[A-Za-z0-9%]{40,}/g;
```

### Extend Injection Pattern Detection

```javascript
this.injectionPatterns.push(
  /act\s+as\s+(?:a\s+)?(?:different|unrestricted)\s+ai/gi,
  /developer\s+mode\s+enabled/gi,
);
```

---

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run AI SAFE² Verification Suite
  run: |
    node smoke_test.js --json > reports/test-results.json
    cat reports/test-results.json | jq '.summary'

- name: Upload SARIF to GitHub Security
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: reports/ai_safe2_results.sarif
```

### Exit Codes

| Code | Meaning |
|:---:|:---|
| `0` | All tests passed |
| `1` | One or more tests failed |

---

## Architecture Philosophy

**Why two layers?**

The governance layer (core/) works because it's loaded first. The LLM reads SOUL.md and GOVERNANCE.md before any user input and internalizes those constraints.

The enforcement layer (enforcement/) works because it doesn't depend on the LLM following instructions. It intercepts at the tool execution level. An LLM that has been compromised by an IPI attack still gets its tool calls blocked by the gateway.

**Why fail-closed?**

Any internal gateway error returns `authorized: false`. Detection-first security fails open when monitors are unavailable. We fail closed. The cost of a false-positive tool block is a retry. The cost of an undetected exfiltration is a breach.

**Why structured JSON logs?**

Plain-text logs are for humans. Structured logs with `control_id`, `category`, and `ts` fields feed SIEM, CI/CD, and evidence generation pipelines. Every blocked event maps back to a specific AI SAFE² control.

---

## Next Steps & Roadmap

| Priority | Item | Complexity |
|:---|:---|:---:|
| P1 | Production rollback wiring (`git reset --hard HEAD`) | Low |
| P1 | Cryptographic signature of IDENTITY.md | Medium |
| P2 | Real-time HITL webhook on ALERT events | Medium |
| P2 | Cryptographic log chaining | High |
| P3 | Subagent identity signing | High |
| P3 | Extend to additional agent frameworks | Medium |

---

## Framework Reference

Built on **AI SAFE² v3.0** — the Sovereign Agent Security Standard.

- Framework docs: [CyberStrategyInstitute/ai-safe2-framework](https://github.com/CyberStrategyInstitute/ai-safe2-framework)
- AISM Maturity Model: See framework repository
- Additional Antigravity examples: `examples/anti-gravity-sovereign-runtime/`

---

*AI SAFE² is a product of the Cyber Strategy Institute.*
*"Policy is just intent. Engineering is reality."*
