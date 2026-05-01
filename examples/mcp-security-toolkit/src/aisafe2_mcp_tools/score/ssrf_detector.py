"""
AI SAFE2 MCP Security Toolkit — mcp-score: SSRF Detector
Detects SSRF surface in MCP tool schemas.
A tool "accepts URL parameters" if its inputSchema contains any field
with url/uri/endpoint/href/target/webhook/callback naming.

Scoring:
  No URL parameters:      5/5
  1–2 URL-accepting tools: 2/5 (risk exists but limited)
  3+ URL-accepting tools:  0/5

CVE reference: CVE-2026-26118 (Azure MCP → AWS IMDS credential theft).
               RAXE-2026-034 (Atlassian SSRF → prompt injection chain).
"""
from __future__ import annotations

import json
import re

from aisafe2_mcp_tools.score.models import CheckResult
from aisafe2_mcp_tools.shared.patterns import SSRF_URL_PATTERNS

_REMEDIATION = (
    "Validate all URL parameters against a blocklist before making requests. "
    "Block 169.254.x.x (AWS IMDS), RFC 1918 ranges, loopback, and file:// URIs. "
    "from aisafe2_mcp_tools.shared.patterns import SSRF_BLOCKED_PATTERNS. "
    "See AI SAFE2 v3.0 CP.5.MCP-6 and CVE-2026-26118."
)


def check_ssrf_surface(tools: list[dict]) -> CheckResult:
    """Analyze tool schemas for SSRF-enabling URL parameters."""
    ssrf_tools = [
        t.get("name", "?") for t in tools
        if any(p.search(json.dumps(t.get("inputSchema", {}))) for p in SSRF_URL_PATTERNS)
    ]

    count = len(ssrf_tools)
    score = 5 if count == 0 else (2 if count <= 2 else 0)

    return CheckResult(
        check_id="SSRF", name="SSRF Surface Detection", cp5_control="MCP-6",
        passed=(score >= 3), score=score, max_score=5,
        severity="high" if count > 0 else "info",
        detail=(
            f"{count} tool(s) accept URL parameters: {', '.join(ssrf_tools[:5])}. "
            "Each is a potential SSRF vector (CVE-2026-26118 pattern)."
            if ssrf_tools else "No URL-accepting parameters detected."
        ),
        remediation=_REMEDIATION if count > 0 else "",
    )
