"""
AI SAFE2 MCP Security Toolkit — mcp-score: Schema Scanner
Analyzes MCP tool schemas for injection patterns and FSP (Full Schema Poisoning).

Two distinct scan surfaces:
  1. Injection scan (MCP-2): checks all string values in tool schemas for
     28 injection pattern families. Score: 20 - deductions per finding.

  2. FSP scan (MCP-2, CyberArk April 2026 research): checks the complete
     raw JSON for Full Schema Poisoning markers. These are different from
     standard injection patterns — they are specifically designed to
     poison model behavior via schema metadata (parameter names, enum
     values, response schemas) rather than description fields.
     Score: 10 if clean, 0 if any FSP marker found.
"""
from __future__ import annotations

import json
from typing import Any

from aisafe2_mcp_tools.score.models import CheckResult
from aisafe2_mcp_tools.shared.patterns import INJECTION_PATTERNS

_INJ_REMEDIATION = (
    "Apply output sanitization to all tool returns: "
    "from aisafe2_mcp_tools.shared.patterns import sanitize_value. "
    "return sanitize_value(result, 'tool_name')[0]. "
    "See AI SAFE2 v3.0 CP.5.MCP-2."
)

_FSP_REMEDIATION = (
    "Audit ALL tool schema fields for FSP markers — not just description fields. "
    "Check parameter names, enum values, and response schemas. "
    "CyberArk FSP research April 2026. See AI SAFE2 v3.0 CP.5.MCP-2."
)


def scan_tool_schemas(tools_data: dict) -> tuple[CheckResult, CheckResult]:
    """
    Scan tool schemas for injection and FSP patterns.
    Returns (injection_check, fsp_check).
    """
    tools = tools_data.get("result", {}).get("tools", [])
    raw_json = json.dumps(tools_data)

    # ── Injection scan ──────────────────────────────────────────────────────
    inj_findings: list[dict] = []
    inj_score = 20

    for tool in tools:
        for field_path, text in _extract_strings(tool, tool.get("name", "?")):
            for pattern in INJECTION_PATTERNS:
                if pattern.regex.search(text):
                    inj_findings.append({
                        "tool": tool.get("name"),
                        "field": field_path,
                        "family": pattern.family,
                        "severity": pattern.severity,
                        "cp5": pattern.cp5_control,
                    })
                    deduction = 20 if pattern.severity == "critical" else 5
                    inj_score = max(0, inj_score - deduction)

    inj_check = CheckResult(
        check_id="INJECTION", name="Tool Injection Scan (MCP-2)", cp5_control="MCP-2",
        passed=(not inj_findings), score=inj_score, max_score=20,
        severity=(
            "critical" if any(f["severity"] == "critical" for f in inj_findings)
            else "high" if inj_findings else "info"
        ),
        detail=(
            f"{len(inj_findings)} injection pattern(s) across {len(tools)} tools."
            if inj_findings else f"No injection patterns in {len(tools)} tools."
        ),
        remediation=_INJ_REMEDIATION if inj_findings else "",
        findings=inj_findings,
    )

    # ── FSP scan ────────────────────────────────────────────────────────────
    fsp_hits = [
        pat.description[:80]
        for pat in INJECTION_PATTERNS
        if pat.family == "fsp_schema_poisoning" and pat.regex.search(raw_json)
    ]
    fsp_check = CheckResult(
        check_id="FSP", name="Full Schema Poisoning (FSP) Scan", cp5_control="MCP-2",
        passed=(not fsp_hits), score=0 if fsp_hits else 10, max_score=10,
        severity="critical" if fsp_hits else "info",
        detail=(
            f"FSP markers detected: {'; '.join(fsp_hits)}" if fsp_hits
            else "No FSP markers detected."
        ),
        remediation=_FSP_REMEDIATION if fsp_hits else "",
    )

    return inj_check, fsp_check


def _extract_strings(obj: Any, prefix: str = "") -> list[tuple[str, str]]:
    """Recursively extract all (path, string_value) pairs from a JSON object."""
    results: list[tuple[str, str]] = []
    if isinstance(obj, str):
        results.append((prefix, obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            results.extend(_extract_strings(v, f"{prefix}.{k}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            results.extend(_extract_strings(item, f"{prefix}[{i}]"))
    return results
