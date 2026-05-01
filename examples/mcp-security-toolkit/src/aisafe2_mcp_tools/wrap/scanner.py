"""
AI SAFE2 MCP Security Toolkit — mcp-safe-wrap: Message Scanner
Injection scanning for MCP JSON-RPC messages.
Shared by STDIO wrapper and HTTP proxy — same scanning logic, different transports.

Uses the shared patterns library (shared/patterns.py) which is the
single source of truth for injection pattern families across the toolkit.
"""
from __future__ import annotations

import json
from typing import Any

from aisafe2_mcp_tools.shared.patterns import (
    SSRF_BLOCKED_PATTERNS,
    sanitize_value,
)


class MessageScanner:
    """
    Scans MCP JSON-RPC messages for injection patterns and SSRF URLs.

    Usage:
        scanner = MessageScanner()
        sanitized_msg, findings = scanner.scan(msg, direction="output")
        ssrf_findings = scanner.check_ssrf(msg)
    """

    def scan(
        self,
        msg: dict,
        direction: str = "output",
    ) -> tuple[dict, list[dict]]:
        """
        Sanitize all string values in a JSON-RPC message.

        Returns:
            (sanitized_msg, findings)
            sanitized_msg: dict with injection patterns redacted
            findings: list of finding dicts (empty if clean)
        """
        sanitized, findings = sanitize_value(msg, f"mcp.{direction}")
        return (
            sanitized if isinstance(sanitized, dict) else msg,
            findings if isinstance(findings, list) else [],
        )

    def check_ssrf(self, obj: Any, path: str = "") -> list[dict]:
        """
        Recursively scan all string values for SSRF-blocked URL patterns.
        Returns list of finding dicts for any matches found.
        """
        findings: list[dict] = []
        if isinstance(obj, str):
            for pattern in SSRF_BLOCKED_PATTERNS:
                if pattern.search(obj):
                    findings.append({
                        "field_path": path,
                        "family": "ssrf_blocked_url",
                        "severity": "critical",
                        "description": f"SSRF-blocked URL at {path}: {obj[:80]}",
                    })
                    break  # One SSRF finding per field
        elif isinstance(obj, dict):
            for k, v in obj.items():
                findings.extend(self.check_ssrf(v, f"{path}.{k}" if path else k))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                findings.extend(self.check_ssrf(item, f"{path}[{i}]"))
        return findings

    def extract_tool_name(self, msg: dict) -> str:
        """Extract tool name from a tools/call message, or empty string."""
        params = msg.get("params", {})
        if isinstance(params, dict):
            return str(params.get("name", ""))
        return ""

    @staticmethod
    def parse_json_line(line: bytes) -> dict | None:
        """
        Parse a bytes line as a JSON object.
        Returns the parsed dict or None if parsing fails or result is not a dict.
        """
        try:
            parsed = json.loads(line.decode("utf-8", errors="replace").strip())
            return parsed if isinstance(parsed, dict) else None
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
            return None
