"""
AI SAFE2 MCP Security Toolkit — mcp-score Report Generator
Produces HTML and JSON reports with before/after view, badge section,
and remediation guidance. Used by mcp-score CLI and batch mode.
"""
from __future__ import annotations

import json
from dataclasses import asdict

from aisafe2_mcp_tools.score.assessor import CheckResult, ScoreReport
from aisafe2_mcp_tools.score.badge import generate_badge_markdown, generate_badge_report_section


# ── Terminal output (Rich) ────────────────────────────────────────────────────

def print_terminal_report(report: ScoreReport) -> None:
    """Print score report to terminal using Rich."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich import box
        console = Console()
    except ImportError:
        print_plain_report(report)
        return

    console.print()
    console.print(Panel(
        f"[bold]AI SAFE2 v3.0 CP.5.MCP — Remote Security Assessment[/bold]\n"
        f"Server: [cyan]{report.server_url}[/cyan]\n"
        f"Assessed: {report.assessment_timestamp} ({report.duration_seconds}s)",
        style="blue",
    ))

    # Score display
    score_color = (
        "bright_green" if report.total_score >= 90 else
        "orange1" if report.total_score >= 70 else
        "yellow" if report.total_score >= 50 else
        "red" if report.total_score >= 30 else
        "bold red"
    )
    console.print(
        f"\n  CP.5.MCP Score: [{score_color}]{report.total_score}/100[/{score_color}] "
        f"— [{score_color}]{report.rating}[/{score_color}]"
    )
    if report.attestation.present:
        console.print(f"  Base (remote): {report.base_score}/100 + Attestation bonus: +{report.attestation_bonus}")
    console.print(f"  Tools scanned: {report.tool_count} | Badge eligible: {'YES' if report.badge_eligible else 'NO'}\n")

    # Checks table
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("Check", style="bold")
    table.add_column("Control", justify="center")
    table.add_column("Result", justify="center")
    table.add_column("Score", justify="right")
    table.add_column("Detail", max_width=55)

    for check in report.checks:
        result_str = "[bright_green]PASS[/bright_green]" if check.passed else (
            "[bold red]FAIL[/bold red]" if check.severity in ("critical", "high") else
            "[yellow]WARN[/yellow]"
        )
        score_str = f"{check.score}/{check.max_score}"
        table.add_row(
            check.name,
            check.cp5_control,
            result_str,
            score_str,
            check.detail[:80] + ("..." if len(check.detail) > 80 else ""),
        )

    console.print(table)

    # Attestation
    if report.attestation.present:
        console.print(f"\n  [green]✓[/green] Builder attestation found (/.well-known/mcp-security.json)")
        console.print(f"    Server: {report.attestation.server_name}")
        console.print(f"    Framework: {report.attestation.framework}")
    else:
        console.print(
            "\n  [yellow]![/yellow] No builder attestation found. "
            "Add /.well-known/mcp-security.json to unlock up to +25 bonus points."
        )

    # Errors
    for err in report.errors:
        console.print(f"  [red]ERROR:[/red] {err}")

    # Badge
    console.print()
    if report.badge_eligible:
        console.print(Panel(
            f"[bold green]BADGE ELIGIBLE[/bold green]\n\n"
            f"Add to your README:\n"
            f"[dim]{generate_badge_markdown(report)}[/dim]\n\n"
            f"Run with --badge to get full implementation guide.",
            title="🏆 AI SAFE2 MCP Badge",
            style="green",
        ))
    else:
        console.print(
            f"  Score {report.total_score}/100 — {100 - report.total_score} points needed for badge eligibility (70+).\n"
            f"  Run [bold]mcp-score {report.server_url} --remediate[/bold] for step-by-step fixes."
        )
    console.print()


def print_plain_report(report: ScoreReport) -> None:
    """Plain text fallback when Rich is not available."""
    print(f"\nAI SAFE2 v3.0 CP.5.MCP — Remote Security Assessment")
    print(f"Server: {report.server_url}")
    print(f"Score: {report.total_score}/100 — {report.rating}")
    print(f"Badge eligible: {'YES' if report.badge_eligible else 'NO'}\n")
    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"  [{status}] {check.cp5_control} {check.name}: {check.score}/{check.max_score}")
        print(f"        {check.detail[:100]}")
    if report.errors:
        for err in report.errors:
            print(f"  ERROR: {err}")


# ── JSON output ───────────────────────────────────────────────────────────────

def to_json(report: ScoreReport) -> str:
    """Serialize report to JSON. Suitable for machine parsing and CI gates."""
    d = {
        "schema": "aisafe2-mcp-score-v1",
        "server_url": report.server_url,
        "assessment_timestamp": report.assessment_timestamp,
        "duration_seconds": report.duration_seconds,
        "scores": {
            "total": report.total_score,
            "base_remote": report.base_score,
            "attestation_bonus": report.attestation_bonus,
            "max_possible": report.max_possible,
        },
        "rating": report.rating,
        "badge_eligible": report.badge_eligible,
        "tool_count": report.tool_count,
        "tools_scanned": report.tools_scanned,
        "framework": "AI SAFE2 v3.0 CP.5.MCP",
        "checks": [
            {
                "check_id": c.check_id,
                "name": c.name,
                "cp5_control": c.cp5_control,
                "passed": c.passed,
                "score": c.score,
                "max_score": c.max_score,
                "severity": c.severity,
                "detail": c.detail,
                "remediation": c.remediation,
                "findings": c.findings,
            }
            for c in report.checks
        ],
        "attestation": {
            "present": report.attestation.present,
            "server_name": report.attestation.server_name,
            "framework": report.attestation.framework,
            "controls_attested": {
                "no_dynamic_commands": report.attestation.no_dynamic_commands,
                "output_sanitization": report.attestation.output_sanitization,
                "source_hash_provided": bool(report.attestation.source_hash),
                "rate_limiting": report.attestation.rate_limiting,
                "audit_logging": report.attestation.audit_logging,
                "network_isolation": report.attestation.network_isolation,
            },
        },
        "errors": report.errors,
        "badge_markdown": generate_badge_markdown(report) if report.badge_eligible else None,
    }
    return json.dumps(d, indent=2)


# ── HTML output ───────────────────────────────────────────────────────────────

def to_html(report: ScoreReport) -> str:
    """Generate a standalone HTML report with before/after view."""
    score_color = (
        "#28a745" if report.total_score >= 90 else
        "#f6921e" if report.total_score >= 70 else
        "#ffc107" if report.total_score >= 50 else
        "#dc3545" if report.total_score >= 30 else
        "#820f1a"
    )

    def row_class(check: CheckResult) -> str:
        if check.passed: return "pass"
        if check.severity in ("critical", "high"): return "fail"
        return "warn"

    def status_badge(check: CheckResult) -> str:
        if check.passed: return '<span class="badge pass">PASS</span>'
        if check.severity in ("critical", "high"): return '<span class="badge fail">FAIL</span>'
        return '<span class="badge warn">WARN</span>'

    checks_html = ""
    for check in report.checks:
        findings_html = ""
        if check.findings:
            findings_html = "<ul class='findings'>" + "".join(
                f"<li><code>{f.get('field','')}</code> — "
                f"<strong>{f.get('family','')}</strong>: {f.get('description','')[:80]}</li>"
                for f in check.findings[:5]
            ) + "</ul>"

        checks_html += f"""
        <tr class="{row_class(check)}">
          <td>{status_badge(check)}</td>
          <td><code>{check.cp5_control}</code></td>
          <td>{check.name}</td>
          <td class="score">{check.score}/{check.max_score}</td>
          <td>{check.detail[:120]}{"..." if len(check.detail) > 120 else ""}</td>
          <td class="remediation">{check.remediation[:100] if not check.passed else ""}</td>
        </tr>
        {f"<tr class='findings-row'><td colspan='6'>{findings_html}</td></tr>" if findings_html else ""}
        """

    att_html = ""
    if report.attestation.present:
        att_html = f"""
        <div class="attestation found">
          <h3>✅ Builder Attestation Found</h3>
          <p>Server: <strong>{report.attestation.server_name}</strong> |
          Framework: {report.attestation.framework} |
          Bonus points: +{report.attestation_bonus}</p>
        </div>"""
    else:
        att_html = """
        <div class="attestation missing">
          <h3>⚠️ No Builder Attestation</h3>
          <p>Add <code>/.well-known/mcp-security.json</code> to unlock up to +25 bonus points
          for controls that cannot be verified remotely (MCP-1, MCP-4, MCP-5, MCP-6).</p>
        </div>"""

    badge_section = generate_badge_report_section(report)
    badge_html = badge_section.replace("\n", "<br>").replace("```", "<code>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI SAFE2 MCP Score — {report.server_url}</title>
<style>
  :root {{
    --orange: #f6921e; --maroon: #820f1a; --navy: #0b1f33;
    --green: #28a745; --red: #dc3545; --yellow: #ffc107; --grey: #6c757d;
  }}
  body {{ font-family: system-ui, sans-serif; margin: 0; background: #f8f9fa; color: #212529; }}
  .header {{ background: var(--navy); color: white; padding: 2rem; }}
  .header h1 {{ margin: 0; font-size: 1.5rem; }}
  .header p {{ margin: 0.5rem 0 0; opacity: 0.8; font-size: 0.9rem; }}
  .score-hero {{ background: white; padding: 2rem; border-bottom: 3px solid {score_color}; text-align: center; }}
  .score-number {{ font-size: 5rem; font-weight: 900; color: {score_color}; line-height: 1; }}
  .score-label {{ font-size: 1.5rem; color: {score_color}; font-weight: 600; }}
  .meta {{ color: var(--grey); font-size: 0.85rem; margin-top: 0.5rem; }}
  .badge-strip {{ background: {"#d4edda" if report.badge_eligible else "#f8d7da"}; padding: 1rem 2rem; border-left: 4px solid {"var(--green)" if report.badge_eligible else "var(--red)"}; margin: 1rem 2rem; border-radius: 4px; }}
  .content {{ padding: 2rem; max-width: 1200px; margin: 0 auto; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.1); }}
  th {{ background: var(--navy); color: white; padding: 0.75rem 1rem; text-align: left; font-size: 0.85rem; }}
  td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #dee2e6; font-size: 0.85rem; vertical-align: top; }}
  tr.pass td {{ background: #f8fff9; }}
  tr.fail td {{ background: #fff8f8; }}
  tr.warn td {{ background: #fffdf0; }}
  tr.findings-row td {{ background: #f8f9fa; padding: 0.25rem 1rem 0.75rem; }}
  .badge.pass {{ background: var(--green); color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.75rem; font-weight: 700; }}
  .badge.fail {{ background: var(--red); color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.75rem; font-weight: 700; }}
  .badge.warn {{ background: var(--yellow); color: #212529; padding: 2px 8px; border-radius: 3px; font-size: 0.75rem; font-weight: 700; }}
  .score {{ font-weight: 700; }}
  .remediation {{ color: var(--maroon); font-size: 0.8rem; }}
  ul.findings {{ margin: 0.25rem 0; padding-left: 1.5rem; font-size: 0.8rem; }}
  .attestation {{ padding: 1rem 1.5rem; border-radius: 6px; margin: 1.5rem 0; }}
  .attestation.found {{ background: #d4edda; border: 1px solid #c3e6cb; }}
  .attestation.missing {{ background: #fff3cd; border: 1px solid #ffeeba; }}
  h2 {{ color: var(--navy); border-bottom: 2px solid var(--orange); padding-bottom: 0.5rem; }}
  .badge-section {{ background: white; padding: 1.5rem; border-radius: 8px; margin-top: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,.1); }}
  .footer {{ background: var(--navy); color: white; padding: 1rem 2rem; text-align: center; font-size: 0.8rem; margin-top: 2rem; }}
  .footer a {{ color: var(--orange); text-decoration: none; }}
  pre {{ background: #f1f3f5; padding: 1rem; border-radius: 4px; overflow-x: auto; font-size: 0.8rem; }}
</style>
</head>
<body>
<div class="header">
  <h1>AI SAFE2 v3.0 CP.5.MCP — Remote Security Assessment</h1>
  <p>{report.server_url} | Assessed: {report.assessment_timestamp} ({report.duration_seconds}s) | {report.tool_count} tools scanned</p>
</div>

<div class="score-hero">
  <div class="score-number">{report.total_score}</div>
  <div class="score-label">{report.rating}</div>
  <div class="meta">out of 100 | AI SAFE2 v3.0 CP.5.MCP
  {f" | Base: {report.base_score} + Attestation: +{report.attestation_bonus}" if report.attestation.present else ""}</div>
</div>

<div class="badge-strip">
  {"🏆 <strong>BADGE ELIGIBLE</strong> — This server scores 70+ and qualifies for the AI SAFE2 MCP badge." if report.badge_eligible else
   f"❌ <strong>Not yet badge eligible</strong> — Score {report.total_score}/100. Minimum 70 required. See remediation below."}
</div>

<div class="content">
  <h2>Assessment Results</h2>
  {att_html}

  <table>
    <thead>
      <tr><th>Status</th><th>Control</th><th>Check</th><th>Score</th><th>Detail</th><th>Remediation</th></tr>
    </thead>
    <tbody>
      {checks_html}
    </tbody>
  </table>

  <div class="badge-section">
    <h2>Badge & Implementation Guide</h2>
    <pre>{badge_section}</pre>
  </div>

  <div style="background:white;padding:1.5rem;border-radius:8px;margin-top:1.5rem;box-shadow:0 1px 4px rgba(0,0,0,.1);">
    <h2>About This Assessment</h2>
    <p>This report was generated by <strong>aisafe2-mcp-tools mcp-score v1.0</strong> against the
    <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework">AI SAFE2 v3.0 framework</a>
    CP.5.MCP controls.</p>
    <p><strong>What remote assessment covers:</strong> Authentication posture, TLS enforcement,
    tool description injection patterns (MCP-2), Full Schema Poisoning (CyberArk research),
    security response headers, application-layer rate limiting, session ID exposure, and SSRF surface.</p>
    <p><strong>What remote assessment cannot cover:</strong> Dynamic command construction in server code (MCP-1),
    source integrity hash (MCP-4), internal audit logging configuration (MCP-5), egress filtering implementation (MCP-6).
    These require builder attestation via <code>/.well-known/mcp-security.json</code> or direct code audit using
    <code>mcp-scan</code>.</p>
    <p><strong>Authorization:</strong> By running this tool, the caller attests that they are authorized to
    assess the target server. mcp-score reads only publicly accessible endpoints and does not modify server state.</p>
  </div>
</div>

<div class="footer">
  <p>AI SAFE2 v3.0 | Cyber Strategy Institute |
  <a href="https://cyberstrategyinstitute.com/ai-safe2/">cyberstrategyinstitute.com/ai-safe2/</a> |
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework">GitHub</a></p>
</div>
</body>
</html>"""
