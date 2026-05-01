# Research Note 024 — MCP Consumer Protection
## AI SAFE2 v3.0 | April 2026 | New

**Status:** New | First publication
**Classification:** TLP:WHITE
**Author:** The Architect | Cyber Strategy Institute

---

## Abstract

Prior MCP security research focused on server-side vulnerabilities and protocol-level design failures. This note addresses the complementary problem: the consumer — the individual, team, or enterprise connecting to MCP servers they do not control — has almost no native protections and no tooling specifically designed for their threat model.

The consumer's threat model is structurally different from the server builder's: consumers cannot audit server source code, cannot verify what happens to their tool call parameters after they leave the proxy, and cannot inspect the MCP server's internal implementation of output sanitization. They are trusting a black box connected to their most capable AI system.

This note establishes the consumer threat model, documents four confirmed consumer-side incidents, and specifies the consumer protection controls implemented in `mcp-safe-wrap`.

---

## The Consumer Threat Model

A consumer connecting to an external MCP server faces five distinct risks that do not affect server operators.

**Supply chain compromise without visible signals.** The September 2025 Postmark incident demonstrated that a consumer can unknowingly connect to a compromised server whose code appears legitimate (the tool invocations work normally), while every processed payload is silently exfiltrated to an attacker-controlled server. The consumer has no direct access to server logs or source code.

**Rug pull without notification.** A server with established trust can mutate its tool descriptions at any time. The consumer's AI client has no mechanism to detect that tool schemas changed between sessions. The injected instructions arrive as trusted tool metadata in the next session.

**Billing amplification as consumer loss.** API costs from Phantom-class attacks accrue to the consumer's account, not the server operator's. The server operator may not be malicious — they may simply not have implemented session cost controls. The consumer carries the financial exposure regardless.

**Cross-server token reuse.** Consumers who use the same OAuth token across multiple MCP connections (the default behavior in many clients) are exposed to CVE-2025-69196 and CVE-2026-27124 class attacks: a malicious server can replay the consumer's token against other services in the consumer's connected stack.

**Persistent memory poisoning.** Tool responses that enter the consumer's agent's persistent memory affect all future sessions. A consumer who processes one malicious tool response may experience degraded agent behavior indefinitely — not just in the session where the injection occurred.

---

## Confirmed Consumer-Side Incidents

**September 2025 — Postmark MCP supply chain.** Email content exfiltrated silently for an unknown period before detection. Consumers had no indication of compromise because tool behavior was functionally correct.

**June 2025 — Asana cross-tenant.** Consumer organizations' data was readable by other tenants' agents. No consumer-side action could prevent or detect this — it was a server-side isolation failure with no consumer-visible signals.

**July 2025 — Cursor agent filesystem destruction.** A developer's agent processed a malicious PR, wiped the local filesystem, and deleted AWS resources. The consumer's agent used the consumer's own credentials. The damage was irreversible.

**November 2025 — Billing amplification ($47,000).** Four agents entered an infinite retry loop. The billing accrued to the consumer (the organization running the agents). The server operator bore no financial consequence.

---

## Consumer Protection Controls

### Runtime: mcp-safe-wrap

The `mcp-safe-wrap` tool provides three consumer-side protections regardless of what the connected server does:

**Output scanning** intercepts tool responses before they reach the LLM client. Injection payloads in tool responses are redacted. This defends against both supply chain compromise (poisoned server code) and rug pull attacks (mutated tool schemas injecting via response bodies).

**SSRF URL blocking** prevents any string value in tool call parameters that matches a known SSRF target (AWS IMDS, RFC 1918, loopback, file://) from reaching the server. This eliminates the consumer's contribution to SSRF exploitation even if the server lacks its own SSRF controls.

**Immutable audit log** records every tool invocation and every injection detection to a JSONL file on the consumer's local filesystem. This provides the only reliable forensic record when server-side logs are unavailable, as in a supply chain compromise.

### Configuration

Connect Claude Code to any external server through `mcp-safe-wrap`:
```bash
mcp-safe-wrap proxy https://external-server.example/mcp --token your-token
```

Connect Claude Code to the proxy instead of the server:
```json
{"type": "http", "url": "http://localhost:8080/proxy"}
```

### Assessment: mcp-score

Before connecting to any external server, consumers can assess its security posture:
```bash
mcp-score https://server.example/mcp
```

A server scoring below 50 should not be connected to any production system. The AI SAFE2 MCP badge (70+ score) is the consumer's signal that a server has implemented the minimum CP.5.MCP standard.

---

## Consumer Configuration Checklist

This checklist is for consumers connecting to external MCP servers, not server operators.

**Immediate (before next session):**
- Audit all MCP configuration files (`claude_desktop_config.json`, `.mcp.json`, `.claude/settings.json`)
- Remove any server not explicitly installed and actively used
- Rotate GitHub, Slack, email, and database credentials that MCP has accessed since January 2026
- Set API cost alerts at 2x expected daily spend

**Before connecting to any new server:**
- Run `mcp-score https://the-server-url.example/mcp`
- Do not connect production systems to servers scoring below 50
- Use `mcp-safe-wrap proxy` for servers scoring below 70
- Ask the server operator for their `.well-known/mcp-security.json` attestation

**Default configuration:**
- Set all MCP connectors to read-only unless write access is explicitly required
- Do not connect write-capable agents (email, GitHub, database) to sessions that also process external content
- Exclude `~/.ssh/`, `~/.aws/`, `~/.config/`, and all `.env` directories from filesystem MCP servers

---

## Relationship to CP.5.MCP

The consumer protection controls specified in this note are implemented as:

- `mcp-safe-wrap` (MCP-2 output sanitization, MCP-6 SSRF, MCP-5 audit log)
- `mcp-score` (MCP-7 zero-trust client configuration assessment)

They are complementary to the server-side controls (MCP-1 through MCP-13). Server-side controls reduce the probability of compromise. Consumer-side controls reduce the impact when compromise occurs.

The full CP.5.MCP specification: [github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/00-cross-pillar](https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/00-cross-pillar)

---

## Open Questions for Future Research

1. **Token binding at the consumer level.** Can consumers enforce audience-restricted tokens independently of server-side OAuth implementation?

2. **Schema pinning.** Can consumers detect rug pull attacks by pinning the `tools/list` hash at initial trust establishment and comparing on each subsequent connection?

3. **Cross-session memory hygiene.** What is the effective blast radius of a single persistent memory poisoning event across a consumer's full agent deployment?

4. **Registry consumer protections.** What consumer-accessible signals exist in MCP registries that would allow risk assessment before first connection?

---

*AI SAFE2 v3.0 | Cyber Strategy Institute | cyberstrategyinstitute.com/ai-safe2/*
