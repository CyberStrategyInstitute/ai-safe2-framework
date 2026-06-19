# Tool Authorization — P1.T2.5
## AI SAFE² v3.0 Function Access Control

---

## Policy

Only tools listed in this file may be invoked by this agent.
The `SovereignLangChain.wrap_tool()` method enforces this at runtime.

**To add a tool:** Update this file, update `AISAFE2_ALLOWED_DOMAINS` in `.env`,
and pass the wrapped tool to the agent via `sovereign.wrap_tool(tool)`.

---

## Authorized Tools

```yaml
# Edit this block for your deployment
authorized_tools:
  - name: "web_search"
    purpose: "Search public web for current information"
    allowed_domains:
      - "api.search-provider.com"
    max_calls_per_session: 20
    class_h: false
    notes: "Returns untrusted content — P1.T1.10 scanned at on_tool_end"

  - name: "read_file"
    purpose: "Read files from the declared workspace"
    allowed_domains: []   # local filesystem only
    max_calls_per_session: 30
    class_h: false
    notes: "Path traversal blocked by P1.T1.2 / check_path_safety()"

  # Add additional tools below
  # - name: "..."
  #   purpose: "..."
  #   allowed_domains: []
  #   max_calls_per_session: 10
  #   class_h: false
```

---

## Domain Allowlist — P1.T2.3

All outbound HTTP calls from tools are validated against this allowlist.

```
# Keep in sync with AISAFE2_ALLOWED_DOMAINS in .env
allowed_domains:
  - api.openai.com
  - api.anthropic.com
  # Add your tool-specific API domains here
```

**Always blocked (not configurable):**
- 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 (RFC 1918)
- 127.0.0.0/8, localhost
- 169.254.169.254 (AWS/GCP/Azure IMDS)
- metadata.google.internal
- IPv6 ULA fd00::/8, ::1

---

## Class-H Tool Actions — CP.10

These tool operations require HEAR authorization before execution:
- File deletion (`delete`, `remove`, `unlink`)
- Writing to paths outside the declared workspace
- Any tool call that makes external POST/PUT/DELETE to production systems

The `check_hear_gate()` method is called automatically on tool inputs
containing Class-H patterns.

---

*AI SAFE² v3.0 | Cyber Strategy Institute | P1.T2.5 Function Access Control*
