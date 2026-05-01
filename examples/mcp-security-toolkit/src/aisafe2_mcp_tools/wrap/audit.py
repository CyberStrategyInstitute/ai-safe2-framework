"""
AI SAFE2 MCP Security Toolkit — mcp-safe-wrap: Audit Log
Immutable JSONL audit writer for MCP tool invocations and security events.

Each record is a single JSON line. The log is append-only.
Audit log failure NEVER crashes the proxy — errors are silently swallowed.

Record schema:
  timestamp:     ISO 8601 UTC
  event:         event type (see EVENT_TYPES below)
  direction:     "input" | "output" (for injection events)
  method:        JSON-RPC method (e.g., "tools/call")
  tool_name:     tool name from params.name
  client_ip:     IP address (HTTP proxy mode only)
  finding_count: number of injection patterns found
  families:      list of injection pattern families detected
  severities:    list of severities detected

AI SAFE2 v3.0 CP.5.MCP-5 compliance:
  Every tool invocation generates an audit record.
  Every injection detection generates an audit record.
  Records are appended to a JSONL file (append-only = immutable).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVENT_TYPES = {
    "tool_invocation",          # Every MCP tools/call (MCP-5)
    "input_injection_detected", # Injection found in inbound message
    "output_injection_detected",# Injection found in outbound message
    "ssrf_blocked",             # SSRF URL blocked in params
    "rate_limited",             # Request rate-limited
    "proxy_start",              # Proxy started (with target URL)
    "proxy_stop",               # Proxy stopped
    "schema_changed",           # tools/list hash changed vs baseline (MCP-11)
    "schema_pinned",            # tools/list hash recorded at session start (MCP-11)
}

# CP.1 taxonomy tags for MCP failure classes (MCP-13).
# Applied to audit records so incident response teams classify correctly.
# cognitive_surface: "model" | "memory" | "both"
# memory_persistence: "session" | "cross_session" | "chronic" | "delayed_days" | "delayed_weeks"
CP1_TAXONOMY: dict[str, dict[str, str]] = {
    "output_injection_detected": {"cognitive_surface": "model",  "memory_persistence": "session"},
    "input_injection_detected":  {"cognitive_surface": "model",  "memory_persistence": "session"},
    "ssrf_blocked":              {"cognitive_surface": "model",  "memory_persistence": "session"},
    "schema_changed":            {"cognitive_surface": "model",  "memory_persistence": "delayed_weeks"},
    "tool_invocation":           {},  # No taxonomy tag — informational event only
    "proxy_start":               {},
    "proxy_stop":                {},
    "schema_pinned":             {},
    "rate_limited":              {},
}


class AuditLog:
    """
    Append-only JSONL audit log.

    Usage:
        log = AuditLog("~/.mcp-safe-wrap/audit.jsonl")
        log.write({"event": "tool_invocation", "tool_name": "lookup_control", ...})
    """

    def __init__(self, path: str | None) -> None:
        self._path: Path | None = None
        if path:
            self._path = Path(path).expanduser().resolve()
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError):
                self._path = None  # Disable logging if path is inaccessible

    def write(self, record: dict[str, Any]) -> None:
        """Append a record to the audit log. Silent on failure.

        Automatically enriches the record with CP.1 taxonomy tags (MCP-13)
        based on the event type, so incident response teams classify correctly.
        """
        if self._path is None:
            return
        record.setdefault("timestamp", _iso_now())
        # MCP-13: Inject CP.1 taxonomy tags where applicable
        event = record.get("event", "")
        taxonomy = CP1_TAXONOMY.get(event, {})
        if taxonomy:
            record.setdefault("cp1_cognitive_surface", taxonomy.get("cognitive_surface", ""))
            record.setdefault("cp1_memory_persistence", taxonomy.get("memory_persistence", ""))
        try:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
        except Exception:
            pass  # Audit log failure must never crash the proxy

    def write_injection(
        self,
        direction: str,
        findings: list[dict],
        method: str = "",
        client_ip: str = "",
        tool_name: str = "",
    ) -> None:
        """Write an injection detection event."""
        self.write({
            "event": f"{direction}_injection_detected",
            "direction": direction,
            "method": method,
            "tool_name": tool_name,
            "client_ip": client_ip,
            "finding_count": len(findings),
            "families": sorted({f.get("family", "") for f in findings if isinstance(f, dict)}),
            "severities": sorted({f.get("severity", "") for f in findings if isinstance(f, dict)}),
        })

    def write_tool_invocation(
        self,
        method: str,
        tool_name: str,
        client_ip: str = "",
    ) -> None:
        """Write a tool invocation audit record (MCP-5 compliance)."""
        self.write({
            "event": "tool_invocation",
            "method": method,
            "tool_name": tool_name,
            "client_ip": client_ip,
        })

    def write_ssrf_blocked(self, field_path: str, client_ip: str = "") -> None:
        """Write an SSRF URL blocked event."""
        self.write({
            "event": "ssrf_blocked",
            "field_path": field_path,
            "client_ip": client_ip,
        })

    def write_schema_pinned(self, schema_hash: str) -> None:
        """Record tools/list baseline hash at session startup (MCP-11)."""
        self.write({
            "event": "schema_pinned",
            "schema_hash": schema_hash,
        })

    def write_schema_changed(self, baseline_hash: str, current_hash: str) -> None:
        """Alert on tools/list hash change vs. pinned baseline (MCP-11 + MCP-13)."""
        self.write({
            "event": "schema_changed",
            "baseline_hash": baseline_hash,
            "current_hash": current_hash,
            "action": "ALERT — schema change without documented release event",
        })

    def write_proxy_start(self, target_url: str, local_port: int) -> None:
        self.write({
            "event": "proxy_start",
            "target_url": target_url,
            "local_port": local_port,
        })

    @property
    def path(self) -> Path | None:
        return self._path


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()
