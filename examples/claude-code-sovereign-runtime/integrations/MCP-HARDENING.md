# MCP Server Hardening Guide -- AI SAFE2

MCP (Model Context Protocol) servers are the highest-risk integration surface for Claude Code after the source map leak. The leaked orchestration code reveals exactly how subagent trust propagates through MCP chains, making adversarial MCP servers a now-documented threat vector.

---

## The MCP Threat Model (Post-Leak)

When `--dangerously-skip-permissions` is active, **all subagents spawned including MCP tool calls inherit full autonomous access**. This cannot be overridden at the subagent level. An adversarial MCP server that returns a prompt injection payload now has a documented path to full code execution.

Even without bypass mode, MCP server responses that contain injection payloads can influence Claude's next actions within the session.

---

## Step 1: Audit Your MCP Connections

```bash
# Find all MCP configs
find ~ -name "*.json" -path "*mcp*" 2>/dev/null | head -20

# Review what MCP servers Claude Code is configured to use
cat ~/.claude/settings.json | grep -A 20 '"mcpServers"'

# Check project-level MCP configs
cat .claude/settings.json 2>/dev/null | grep -A 20 '"mcpServers"'
```

**For every MCP server you find, answer:**
1. Do I control the source code of this server?
2. Does it make outbound network calls?
3. What data does it have access to?
4. Is it receiving input from untrusted sources (web, user content, external APIs)?

---

## Step 2: Wrap Untrusted MCP Servers with the Proxy

For any MCP server you do not fully control or that fetches external data:

```json
{
  "mcpServers": {
    "my-untrusted-server": {
      "command": "bash",
      "args": [
        "/path/to/integrations/mcp-proxy.sh",
        "--",
        "node",
        "/path/to/server.js"
      ],
      "env": {
        "CLAUDE_CODE_LOG_DIR": "~/.claude/logs"
      }
    }
  }
}
```

---

## Step 3: Harden Your Own MCP Servers

If you maintain MCP servers, apply these controls:

### Input Validation
```javascript
// Validate all tool call inputs against a strict schema
const Ajv = require('ajv');
const ajv = new Ajv({ strict: true, additionalProperties: false });

function validateToolInput(toolName, input) {
  const schema = TOOL_SCHEMAS[toolName];
  if (!schema) throw new Error(`Unknown tool: ${toolName}`);
  const valid = ajv.validate(schema, input);
  if (!valid) throw new Error(`Invalid input: ${ajv.errorsText()}`);
  return input;
}
```

### Output Sanitization
```javascript
// Before returning results to Claude, strip injection patterns
function sanitizeOutput(text) {
  const INJECTION_PATTERNS = [
    /ignore\s+(previous|all|prior)\s+instructions/gi,
    /you\s+are\s+now\s+/gi,
    /dangerously.skip.permissions/gi,
    /\x{200B}-\x{200F}/gu,  // Zero-width chars
  ];

  let sanitized = text;
  for (const pattern of INJECTION_PATTERNS) {
    if (pattern.test(sanitized)) {
      console.error('[SAFE2] Injection pattern detected in output:', pattern);
      sanitized = sanitized.replace(pattern, '[REDACTED_BY_SAFE2]');
    }
  }
  return sanitized;
}
```

### Rate Limiting
```javascript
// Prevent an AI session from flooding your MCP server
const rateLimit = new Map();

function checkRateLimit(sessionId, toolName) {
  const key = `${sessionId}:${toolName}`;
  const now = Date.now();
  const windowMs = 60_000; // 1 minute
  const maxCalls = 20;

  const calls = rateLimit.get(key) || [];
  const recent = calls.filter(t => now - t < windowMs);

  if (recent.length >= maxCalls) {
    throw new Error(`Rate limit exceeded for ${toolName}`);
  }

  recent.push(now);
  rateLimit.set(key, recent);
}
```

---

## Step 4: Network Isolation for MCP Servers

```bash
# Run MCP servers with restricted network access using network namespaces (Linux)
# This prevents an adversarial MCP server from making outbound calls

# Option A: firejail (easy, available via apt)
sudo apt install firejail
firejail --net=none -- node /path/to/mcp-server.js

# Option B: systemd service with network restrictions
# See integrations/mcp-server.service for a template

# Option C: Docker with no external network
docker run --network=none -i my-mcp-server-image
```

---

## Step 5: Monitor MCP Traffic

```bash
# Watch the MCP proxy log in real time
tail -f ~/.claude/logs/mcp-proxy.log

# Check for injection alerts
tail -f ~/.claude/logs/mcp-alerts.log

# Summarize MCP activity for a session
grep "MCP_RESPONSE" ~/.claude/logs/mcp-proxy.log | wc -l
grep "MCP_INJECTION" ~/.claude/logs/mcp-alerts.log
```

---

## Red Flags in MCP Server Behavior

Terminate the MCP connection and investigate if you see:
- Responses much larger than expected for the tool called
- JSON responses with unexpected fields (especially instruction-like text)
- Tool calls that Claude did not explicitly invoke being returned as results
- Any response containing "ignore previous", "you are now", or bypass keywords
- Large base64 blobs in tool results that were not expected

---

## Known Vulnerable MCP Integration Patterns

| Pattern | Risk | Mitigation |
|---|---|---|
| MCP server fetches from user-supplied URLs | High: SSRF + injection | Allowlist URLs, sanitize responses |
| MCP server reads from shared/untrusted repos | High: poisoned README/comments | Scan content before returning |
| MCP server with write access + Claude in bypass mode | Critical: full RCE | Never combine these |
| Multiple MCP servers in one session | Medium: cross-server injection | Isolate servers per session |
| MCP server receiving Slack/email content | Medium: indirect injection | Sanitize all external content |

---

*Cyber Strategy Institute -- AI SAFE2 Framework*
