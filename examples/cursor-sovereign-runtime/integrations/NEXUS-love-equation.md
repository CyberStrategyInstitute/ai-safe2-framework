# NEXUS Love Equation — Cursor Integration
## AI SAFE2 v3.0 | Cyber Strategy Institute

## MCPoison State Tracking (Cursor-Unique)

The Cursor runtime adds MCPoison detection state beyond the standard Love Equation:

```python
status = guard.get_status()
# {
#   "love_score": 94.0,
#   "alignment_band": "GREEN",
#   "violations": 3,
#   "approved_mcp_servers": ["github-mcp", "notion-mcp"],  # ← Cursor-unique
#   "chain_length": 3
# }
```

`approved_mcp_servers` tracks which servers have been approved and their
command hash. Any re-registration with a changed command = MCPoison detection.
This state persists per session — clear between IDE restarts.

## Pipeline Gate for Cursor (Enterprise)

```python
status = guard.get_status()
band   = status["alignment_band"]

# For Cursor enterprise: require GREEN + minimum version
if band != "GREEN":
    print(f"CURSOR GATE BLOCKED: Band={band}")
    sys.exit(1)

# Also enforce minimum Cursor version via MDM
print(f"Cursor gate cleared: Love Score={status['love_score']}")
```

## Version Enforcement (Highest-Leverage Single Action)

From Repello May 2026: "The single highest-leverage hardening move is
pinning to Cursor 2.5 or later via MDM. That closes CVE-2026-26268
(CVSS 9.9), all 2025 MCP CVEs, and the .cursorignore / case-sensitivity
classes in one push."

```python
guard = CursorSovereignRuntime(require_version="2.5")
# Enforce via MDM/fleet management separately
# AI SAFE2 runtime doesn't enforce version — flag it for your MDM
```

## Unified Score

```python
from enforcement.ai_safe2_engine import AISAFE2Engine
from enforcement.sovereign_cursor import CursorSovereignRuntime

shared_engine = AISAFE2Engine(session_id="enterprise-session-001")
cursor_guard = CursorSovereignRuntime()
cursor_guard._engine = shared_engine  # inject shared engine
```
