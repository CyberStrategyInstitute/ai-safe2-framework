# Integration Guide — AI SAFE² for Antigravity 2.0

This guide is for developers integrating the sovereign runtime into a live Antigravity workspace. It covers session initialization, tool wiring, configuration, and common failure modes.

---

## Prerequisites

| Requirement | Version | Notes |
|:---|:---|:---|
| Antigravity | 2.0+ | `agy-node` must be available in PATH |
| Node.js | 18+ | Or use `agy-node` (bundled Electron-Node) |
| OS | Windows 11 + WSL2 or Linux | Deploy script targets Windows |
| Git | Any | Required for rollback wiring |

---

## Installation

### Option A: 1-Click Windows Deployer

```powershell
# Run from repo root in PowerShell
.\deploy.ps1
```

The deployer will:
1. Detect `agy-node` in PATH or `%APPDATA%\Antigravity\bin`
2. Verify directory structure
3. Run the 13-scenario test suite
4. Report compliance status

### Option B: Manual (WSL2 / Linux)

```bash
# Clone or copy the suite into your workspace
cp -r anti-gravity-sovereign-runtime/ /path/to/your/workspace/
cd /path/to/your/workspace/

# Run verification
node smoke_test.js
```

---

## Step 1: Wire the Governance Layer

> ⚠️ **Important:** `core/*.md` files are project files — Antigravity confirmed they are **not** pre-loaded into context by default. Without explicit wiring, the governance layer is documentation, not active enforcement. Choose an option below.

---

### Option 1 — Native Plugin (Recommended)

Loads governance constraints automatically for **every session across all projects**.

```powershell
.\config\install-option1-plugin.ps1
```

- Copies `plugins/governance-enforcer/` to the Antigravity plugin directory
- Plugin has `"autoLoad": true` — loads before every session
- Restart Antigravity after install

**Rollback:**
```powershell
Remove-Item "$env:USERPROFILE\.gemini\config\plugins\governance-enforcer" -Recurse -Force
```

---

### Option 3 — System Prompt Config Injection

Injects governance block directly into the `system_prompt` key in the global Antigravity config. Creates a dated backup before modifying.

```powershell
.\config\install-option3-system-prompt.ps1
```

- Works independently of the plugin system
- Governance is in the context window before any tool execution
- Restart Antigravity after install

---

### Complementary: `.agent/rules/` Workspace Files

Already present in this repo. Antigravity auto-loads `*.md` files from `.agent/rules/` for this workspace with no installation needed:

```
.agent/rules/governance-soul.md             # Hard limits + escalation
.agent/rules/governance-identity-tools.md   # Identity + tool authorization
.agent/rules/governance-memory-context.md   # Memory + context isolation
```

These activate automatically when this project is open. They reinforce Options 1 and 3.

---

### What Each Governance File Defines

| File | AI SAFE² Control | Purpose |
|:---|:---:|:---|
| `IDENTITY.md` | CP.4 | Agent ID, role, trust class, persona lock |
| `SOUL.md` | S1.4 | Hard limits, escalation protocol, credential hygiene |
| `GOVERNANCE.md` | P1 | Context separation, file access, subagent policy |
| `TOOLS.md` | S1.3 | Permitted tools, denied tools, command prefix whitelist |
| `USER.md` | P4.HITL | Human handler profile, confirmation requirements |
| `MEMORY.md` | S1.5 | Memory model, sanitization rules, anchor-memory.json |

---

## Tool Call Wiring

### Where to Integrate the Gateway

The gateway must intercept every tool call. In an MCP-based architecture, insert it as middleware:

```javascript
// mcp_middleware.js
const SafeGateway = require('./enforcement/safe_gateway');

const gateway = new SafeGateway({
  workspaceRoot: process.env.AGY_WORKSPACE_ROOT || process.cwd(),
  whitelistedDomains: [
    'github.com',
    'api.github.com',
    'raw.githubusercontent.com',
    // Add your project-specific APIs here
  ],
  whitelistedCommandPrefixes: [
    'echo', 'date', 'git', 'agy-node', 'npm', 'node',
    // Add safe commands here — be conservative
  ],
});

/**
 * Drop-in MCP tool interceptor.
 * Add this before every tool.call() invocation.
 */
function gatewayCheck(toolName, toolPayload) {
  // Map MCP tool names to gateway action types
  const actionMap = {
    'read_file':              'view_file',
    'write_file':             'write_to_file',
    'edit_file':              'replace_file_content',
    'execute_command':        'run_command',
    'fetch_url':              'read_url_content',
  };

  const action = actionMap[toolName] || toolName;
  const payload = typeof toolPayload === 'string' ? toolPayload : JSON.stringify(toolPayload);

  const result = gateway.verifyAction(action, payload);
  if (!result.authorized) {
    throw new Error(`[AI SAFE² BLOCKED] ${toolName}: ${result.message}`);
  }
}

module.exports = { gatewayCheck };
```

### Input Sanitization Hook

Sanitize all external content before it enters the context window:

```javascript
function sanitizeExternalContent(content, source) {
  const { sanitized, isFlagged, matches } = gateway.sanitizeInput(content);
  if (isFlagged) {
    console.warn(`[IPI WARNING] Content from ${source} flagged for injection attempt`);
    // Optional: halt processing entirely for high-confidence sources
  }
  return sanitized;
}

// Use for: URL fetch results, file reads from untrusted paths, user-pasted content
const safeContent = sanitizeExternalContent(fetchedContent, 'https://example.com/page');
```

---

## Circuit Breaker Wiring

### Register Every Tool Call

```javascript
const CircuitBreaker = require('./enforcement/circuit_breaker');

const breaker = new CircuitBreaker(
  5,     // max identical calls before trip
  5000,  // time window in ms
);

// Wrap every tool dispatch:
async function dispatchTool(toolName, args) {
  // Loop detection
  const loopCheck = breaker.registerCall(toolName, args);
  if (loopCheck.tripped) {
    breaker.triggerRollback();
    throw new Error(loopCheck.reason);
  }
  // ... execute tool
}
```

### Subagent Spawn Guard

```javascript
async function spawnSubagent(config) {
  const check = breaker.validateSubagentSpawn({
    agentName:   config.name,
    mode:        config.mode,       // must be 'sandboxed'
    permissions: config.permissions,
  });

  if (!check.authorized) {
    throw new Error(`Subagent spawn blocked: ${check.reason}`);
  }

  // ... proceed with spawn
}
```

### Memory Write Guard

```javascript
async function writeToMemory(content, filePath) {
  const check = breaker.validateMemoryWrite(content);
  if (!check.safe) {
    throw new Error(`Memory write blocked: ${check.reason}`);
  }
  fs.writeFileSync(filePath, content, 'utf8');
}
```

---

## Customizing for Your Workspace

### Domain Allowlist Configuration

Antigravity workspaces commonly need additional domains. Add them at initialization:

```javascript
const gateway = new SafeGateway({
  whitelistedDomains: [
    'github.com',
    'api.github.com',
    'raw.githubusercontent.com',
    'npmjs.com',
    'registry.npmjs.org',
    'api.openai.com',            // if using OpenAI tools
    'api.anthropic.com',         // if using Anthropic tools
    'your-internal-api.com',     // project-specific
  ],
});
```

**Do not add wildcard entries.** `*.company.com` is less secure than `api.company.com`. Be specific.

### Workspace Root Configuration

The path traversal check resolves all file paths against `workspaceRoot`. Set this to the absolute path of your Antigravity scratch directory:

```javascript
// Windows (via WSL2)
const gateway = new SafeGateway({
  workspaceRoot: '/mnt/c/Users/youruser/.gemini/antigravity/scratch',
});

// Linux / WSL2 native
const gateway = new SafeGateway({
  workspaceRoot: '/home/youruser/projects/workspace',
});
```

### Extending Secret Detection

The default patterns cover GitHub, AWS, Stripe, OpenAI, Anthropic. Add patterns for your stack:

```javascript
// In safe_gateway.js constructor, or extend via subclass:
gateway.secretPatterns['GCP Service Account'] = /"type":\s*"service_account"/g;
gateway.secretPatterns['Databricks Token'] = /dapi[a-zA-Z0-9]{32}/g;
gateway.secretPatterns['Slack Token'] = /xox[baprs]-[0-9a-zA-Z]{10,}/g;
```

---

## Verifying Your Integration

### Full Test Suite

```bash
node smoke_test.js
```

All 13 tests must pass. Note that the path traversal tests (T2.01, T2.02) use the smoke_test.js directory as workspace root by default.

### Tier-Specific Tests

```bash
# Core controls only (fastest, for CI)
node smoke_test.js --tier 1

# Path and network tests
node smoke_test.js --tier 2

# Governance and memory tests
node smoke_test.js --tier 3
```

### CI/CD Integration

```bash
# JSON output for pipeline parsing
node smoke_test.js --json | jq '.summary'

# Expected:
# {
#   "total": 13,
#   "passed": 13,
#   "failed": 0
# }
```

Exit code `0` = all passed. Exit code `1` = failures. Use in any CI system that reads exit codes.

---

## Common Failure Modes

### Gateway Blocks a Legitimate Command

**Symptom:** Your deployment command (`npm run build`) gets blocked.

**Fix:** Add the binary to `whitelistedCommandPrefixes`:

```javascript
whitelistedCommandPrefixes: ['npm', 'node', 'git', 'echo', 'date', 'agy-node'],
```

### Path Traversal False Positive on Symlinked Workspace

**Symptom:** Agent can't read files in a symlinked project directory.

**Fix:** Resolve the real path before passing to the gateway:

```javascript
const realPath = fs.realpathSync(linkPath);
const check = gateway.verifyAction('view_file', realPath);
```

### Circuit Breaker Trips Too Quickly on Batch Operations

**Symptom:** Legitimate batch file processing triggers the loop detector.

**Fix:** Increase the threshold or widen the time window:

```javascript
// Allow 20 identical calls within 30 seconds
const breaker = new CircuitBreaker(20, 30000);
```

Or differentiate calls by including an index in the args:

```javascript
breaker.registerCall('write_to_file', { path: filePath, index: i });
```

### SARIF Not Uploading to GitHub

**Symptom:** `codeql-action/upload-sarif` fails with schema error.

**Fix:** Verify the SARIF schema version matches GitHub's expected `2.1.0`. The generated file uses the correct version — check that no post-processing altered it.

---

## Troubleshooting Audit Log

The audit log at `enforcement/audit.log` is your primary debugging tool. Each line is a JSON object:

```json
{
  "ts": "2026-06-09T14:23:11.042Z",
  "level": "ALERT",
  "control_id": "P1.PATH",
  "category": "PATH_TRAVERSAL_BLOCKED",
  "message": "Path '../../../etc/passwd' resolves outside workspace root"
}
```

**Key fields:**
- `control_id` — the AI SAFE² control that fired
- `category` — machine-readable event type for SIEM filtering
- `level` — INFO (normal), WARN (suspicious), ALERT (blocked), ERROR (internal)

**Common alert categories and what they mean:**

| Category | Control | Action Needed |
|:---|:---|:---|
| `INJECTION_DETECTED` | P1.INJECT | Review source of external content |
| `EXFILTRATION_PREVENTED` | P4.EXFIL | Audit which tool triggered the request |
| `CREDENTIAL_LEAK_BLOCKED` | P1.SECRET | Find and remove hardcoded credential |
| `PATH_TRAVERSAL_BLOCKED` | P1.PATH | Verify file path construction logic |
| `SYMLINK_ESCAPE_BLOCKED` | P1.PATH | Remove symlinks from workspace or use `realpathSync` |
| `PRIVATE_IP_BLOCKED` | P1.DOMAIN | Verify no SSRF vectors in agent code |
| `CIRCUIT_BREAKER_TRIGGERED` | F3.2 | Check for infinite loops in tool orchestration |
| `SUBAGENT_ESCALATION_BLOCKED` | P1.SUBAGENT | Review subagent spawn configuration |
| `MEMORY_POISONING_BLOCKED` | P1.MEMORY | Check source of memory content being written |

---

## Security Boundaries — What This Suite Does NOT Protect

Be explicit. This suite hardens a specific threat surface. It does not cover:

- **LLM model-level jailbreaks** — model fine-tuning or adversarial prompts that bypass alignment at the weights level. This suite operates at the tool execution layer.
- **OS-level exploits** — if the host system is compromised, the gateway cannot prevent an attacker with direct filesystem access.
- **Antigravity platform vulnerabilities** — this suite secures the agent's behavior, not the Antigravity platform binary itself.
- **Social engineering of the human operator** — USER.md defines trust controls but cannot prevent the operator from manually overriding them.
- **Supply chain attacks on npm dependencies** — this suite has no external runtime dependencies, but your project's dependencies are out of scope.

---

## Support & Feedback

- Framework: [CyberStrategyInstitute/ai-safe2-framework](https://github.com/CyberStrategyInstitute/ai-safe2-framework)
- Issues: Open a GitHub issue against the main framework repository
- Controls questions: Reference `controls/policy.yaml` for control definitions and gap documentation

---

_"Detection is a strategy of hope. Certainty is a strategy of engineering."_
_— AI SAFE² Framework Principles_
