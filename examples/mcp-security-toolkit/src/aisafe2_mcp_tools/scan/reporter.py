"""
AI SAFE2 MCP Security Toolkit — mcp-scan: Report Generator
Produces terminal, JSON, and HTML output from scan findings.

Separated from analyzer.py so output format can be changed without
touching the analysis logic. Both consume the same Finding data model.
"""
from __future__ import annotations

import json
from pathlib import Path

from aisafe2_mcp_tools.scan.findings import Finding, SEVERITY_ORDER


_SEVERITY_ICONS = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🔵",
}

_SEVERITY_COLORS = {
    "critical": "#dc3545",
    "high": "#fd7e14",
    "medium": "#ffc107",
    "low": "#0dcaf0",
}


def terminal_report(findings: list[Finding], target: str) -> str:
    """Generate a terminal-readable report string."""
    if not findings:
        return (
            f"\n✅ mcp-scan — No findings in {target}\n\n"
            "AI SAFE2 v3.0 CP.5.MCP static analysis passed.\n"
            "Note: Static analysis is not a substitute for mcp-score (remote assessment)\n"
            "or manual security review. Schedule both for pre-production deployments.\n"
        )

    by_sev: dict[str, list[Finding]] = {
        "critical": [], "high": [], "medium": [], "low": []
    }
    for f in findings:
        by_sev.get(f.severity, by_sev["low"]).append(f)

    lines = [
        f"\nmcp-scan — AI SAFE2 v3.0 CP.5.MCP Static Analysis",
        f"Target: {target}",
        f"Findings: {len(findings)} total | "
        f"{len(by_sev['critical'])} critical · "
        f"{len(by_sev['high'])} high · "
        f"{len(by_sev['medium'])} medium · "
        f"{len(by_sev['low'])} low",
        "",
    ]

    for sev in ("critical", "high", "medium", "low"):
        if not by_sev[sev]:
            continue
        icon = _SEVERITY_ICONS[sev]
        label = sev.upper()
        if sev == "critical":
            label += " — Manual fix required. NEVER auto-fix. Understand the code first."
        lines.append(f"{icon} {label}")
        lines.append("")
        for finding in by_sev[sev]:
            lines.append(f"  [{finding.finding_id}] {finding.title}")
            lines.append(f"  File:        {finding.file}:{finding.line}")
            lines.append(f"  Code:        {finding.code_snippet[:100]}")
            lines.append(f"  Why it matters: {finding.description[:150]}")
            lines.append(f"  Fix:         {finding.remediation[:150]}")
            if finding.cve_refs:
                lines.append(f"  CVEs:        {', '.join(finding.cve_refs)}")
            if finding.manual_required:
                lines.append("  ⚠️  MANUAL REVIEW REQUIRED — review the code before making changes")
            lines.append("")

    lines += [
        "AI SAFE2 v3.0 CP.5.MCP gaps: " + ", ".join(sorted({f.cp5_control for f in findings})),
        "",
        "Next steps:",
        "  mcp-scan fix --interactive   → step through fixes interactively",
        "  mcp-scan fix --auto          → apply safe auto-fixes (HIGH and below only)",
        "  mcp-score <deployed-url>     → remote assessment of deployed server",
    ]
    return "\n".join(lines)


def json_report(findings: list[Finding], target: str) -> str:
    """Generate a machine-readable JSON report."""
    by_sev: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1

    return json.dumps({
        "schema": "aisafe2-mcp-scan-v1",
        "target": target,
        "finding_count": len(findings),
        "by_severity": by_sev,
        "cp5_controls_affected": sorted({f.cp5_control for f in findings}),
        "cves_detected": sorted({cve for f in findings for cve in f.cve_refs}),
        "findings": [f.to_dict() for f in findings],
        "remediation_required": any(f.manual_required for f in findings),
    }, indent=2)


def html_report(findings: list[Finding], target: str) -> str:
    """Generate a standalone HTML report."""
    by_sev: dict[str, list[Finding]] = {
        "critical": [], "high": [], "medium": [], "low": []
    }
    for f in findings:
        by_sev.get(f.severity, by_sev["low"]).append(f)

    rows = ""
    for sev in ("critical", "high", "medium", "low"):
        for finding in by_sev[sev]:
            color = _SEVERITY_COLORS[sev]
            badge = f'<span style="background:{color};color:{"#fff" if sev != "medium" else "#000"};padding:2px 8px;border-radius:3px;font-size:.75rem;font-weight:700">{sev.upper()}</span>'
            cves = ", ".join(finding.cve_refs) if finding.cve_refs else "—"
            rows += f"""
            <tr>
              <td>{badge}</td>
              <td><code>{finding.finding_id}</code></td>
              <td><code>{finding.cp5_control}</code></td>
              <td>{finding.title}</td>
              <td><code>{finding.file}:{finding.line}</code></td>
              <td style="font-size:.8rem;color:#820f1a">{finding.remediation[:120]}</td>
              <td style="font-size:.75rem">{cves}</td>
            </tr>"""

    total = len(findings)
    has_critical = bool(by_sev["critical"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>mcp-scan — {target}</title>
<style>
  body {{font-family:system-ui,sans-serif;margin:0;background:#f8f9fa}}
  .header {{background:#0b1f33;color:#fff;padding:1.5rem 2rem}}
  .header h1 {{margin:0;font-size:1.3rem}}
  .summary {{background:{"#fff3cd" if has_critical else "#d4edda"};padding:1rem 2rem;
             border-left:4px solid {"#dc3545" if has_critical else "#28a745"}}}
  .content {{padding:2rem;max-width:1400px;margin:0 auto}}
  table {{width:100%;border-collapse:collapse;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.1)}}
  th {{background:#0b1f33;color:#fff;padding:.6rem 1rem;text-align:left;font-size:.8rem}}
  td {{padding:.6rem 1rem;border-bottom:1px solid #dee2e6;vertical-align:top;font-size:.82rem}}
  .footer {{background:#0b1f33;color:#fff;padding:1rem 2rem;text-align:center;font-size:.8rem;margin-top:2rem}}
  .footer a {{color:#f6921e}}
</style>
</head>
<body>
<div class="header">
  <h1>mcp-scan — AI SAFE2 v3.0 CP.5.MCP Static Analysis</h1>
  <p style="margin:.4rem 0 0;opacity:.8;font-size:.85rem">Target: {target} | {total} findings</p>
</div>
<div class="summary">
  {"⚠️ <strong>CRITICAL findings present.</strong> Manual review required before deployment." if has_critical else
   f"✅ {total} findings detected. Review and apply fixes before deployment." if total else
   "✅ No findings. Proceed to remote assessment: <code>mcp-score &lt;your-url&gt;</code>"}
</div>
<div class="content">
  <table>
    <thead><tr>
      <th>Severity</th><th>ID</th><th>Control</th><th>Finding</th>
      <th>Location</th><th>Remediation</th><th>CVEs</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>
<div class="footer">
  AI SAFE2 v3.0 | Cyber Strategy Institute |
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/examples/mcp-security-toolkit">
    github.com/CyberStrategyInstitute/ai-safe2-framework
  </a>
</div>
</body>
</html>"""
