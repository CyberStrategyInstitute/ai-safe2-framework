"""
AI SAFE2 MCP Security Toolkit — mcp-score: Security Header Checker
Checks response headers for CP.5.MCP-6 compliance.
2 points per header, max 10. Server header removal counts as a header.

Required headers:
  Strict-Transport-Security (HSTS)
  X-Frame-Options
  X-Content-Type-Options
  Referrer-Policy
  Server header absent (removal = hardening signal)
"""
from __future__ import annotations

from aisafe2_mcp_tools.score.models import CheckResult

_REQUIRED_HEADERS = [
    ("strict-transport-security", "HSTS"),
    ("x-frame-options", "X-Frame-Options"),
    ("x-content-type-options", "X-Content-Type-Options"),
    ("referrer-policy", "Referrer-Policy"),
]

_REMEDIATION = (
    "Add to your reverse proxy (Caddy example in README): "
    "Strict-Transport-Security: max-age=31536000, "
    "X-Frame-Options: DENY, X-Content-Type-Options: nosniff, "
    "Referrer-Policy: strict-origin. Remove Server header. "
    "See AI SAFE2 v3.0 CP.5.MCP-6."
)


def check_security_headers(headers: dict[str, str]) -> CheckResult:
    """
    Check response headers against CP.5.MCP-6 security requirements.
    Accepts a headers dict (keys lowercased).
    """
    headers_lower = {k.lower(): v for k, v in headers.items()}
    score = 0
    present: list[str] = []
    missing: list[str] = []

    for header_name, label in _REQUIRED_HEADERS:
        if header_name in headers_lower:
            score += 2
            present.append(label)
        else:
            missing.append(label)

    if "server" not in headers_lower:
        score += 2
        present.append("Server header removed")
    else:
        missing.append(f"Server header exposed: '{headers_lower.get('server', '')}'")

    detail_parts = []
    if present:
        detail_parts.append(f"Present: {', '.join(present)}")
    if missing:
        detail_parts.append(f"Missing: {', '.join(missing)}")

    return CheckResult(
        check_id="HEADERS", name="Security Response Headers", cp5_control="MCP-6",
        passed=(score >= 8), score=min(10, score), max_score=10,
        severity="medium" if score < 8 else "info",
        detail=". ".join(detail_parts) if detail_parts else "No headers available.",
        remediation=_REMEDIATION if score < 8 else "",
    )
