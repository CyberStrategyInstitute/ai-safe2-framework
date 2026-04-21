"""
AI SAFE² v3.0 Scanner CLI
Usage: python -m scanner.cli scan <path> [OPTIONS]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click

try:
    from .scanner import StaticScanner
    from .report import ISO42001Report
except ImportError:
    from scanner import StaticScanner
    from report import ISO42001Report


SEVERITY_COLORS = {
    "CRITICAL": "\033[91m",  # red
    "HIGH":     "\033[93m",  # yellow
    "MEDIUM":   "\033[94m",  # blue
    "LOW":      "\033[92m",  # green
    "INFO":     "\033[0m",
}
RESET = "\033[0m"
BOLD = "\033[1m"


def _color(text: str, severity: str) -> str:
    return f"{SEVERITY_COLORS.get(severity, '')}{text}{RESET}"


@click.group()
def cli():
    """AI SAFE² v3.0 Static Analysis Scanner\n
    Scans code and configs against 161 AI SAFE² v3.0 controls across
    5 pillars and the Cross-Pillar Governance layer (CP.1-CP.10).
    """
    pass


@cli.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--tier", default="Tier1",
              type=click.Choice(["Tier1", "Tier2", "Tier3"]),
              help="Failure threshold tier. Tier3=strict (fail <90), Tier2=balanced (fail <70), Tier1=baseline (fail <50)")
@click.option("--report", "report_format", default=None,
              type=click.Choice(["json", "sarif", "both"]),
              help="Generate compliance report artifact")
@click.option("--output", default="ai_safe2_audit_report.json",
              help="Output path for the compliance report")
@click.option("--fail-under", default=None, type=float,
              help="Fail with exit code 1 if score is below this value (overrides --tier)")
@click.option("--controls-json", default=None,
              help="Path to ai-safe2-controls-v3.0.json (auto-detected if omitted)")
@click.option("--quiet", is_flag=True, help="Suppress console output (report only)")
@click.option("--show-passes", is_flag=True, help="Show controls that passed (for full audit output)")
@click.option("--max-findings", default=50, help="Maximum findings to display in console (default: 50)")
def scan(path, tier, report_format, output, fail_under, controls_json, quiet, show_passes, max_findings):
    """Scan a project path against AI SAFE² v3.0 controls.

    \b
    Examples:
      python -m scanner.cli scan .
      python -m scanner.cli scan ./my-agent --tier Tier2 --report json
      python -m scanner.cli scan . --fail-under 80 --report both
      python -m scanner.cli scan . --tier Tier3 --quiet --report json --output report.json
    """
    if not quiet:
        click.echo(f"\n{BOLD}AI SAFE² v3.0 Scanner{RESET}")
        click.echo(f"Target: {path}")
        click.echo("─" * 60)

    scanner = StaticScanner(controls_json=controls_json)
    result = scanner.scan_project(path)

    if not quiet:
        _print_results(result, max_findings)

    # Generate report
    if report_format in ("json", "both"):
        reporter = ISO42001Report()
        reporter.generate_report(result, output_path=output, include_sarif=False)

    if report_format in ("sarif", "both"):
        reporter = ISO42001Report()
        sarif_path = output.replace(".json", ".sarif.json") if output.endswith(".json") else output + ".sarif.json"
        reporter.generate_report(result, output_path=output, include_sarif=True)

    # Determine failure
    if fail_under is not None:
        should_fail = result.score < fail_under
    else:
        should_fail = _tier_fail(result, tier)

    if should_fail:
        if not quiet:
            click.echo(f"\n{BOLD}❌ SCAN FAILED — Score {result.score}/100 below threshold{RESET}")
        sys.exit(1)
    else:
        if not quiet:
            click.echo(f"\n{BOLD}✅ SCAN PASSED — Score {result.score}/100{RESET}")


def _tier_fail(result, tier: str) -> bool:
    if tier == "Tier3" and result.score < 90:
        return True
    if tier == "Tier2" and result.score < 70:
        return True
    if tier == "Tier1" and result.score < 50:
        return True
    return False


def _print_results(result, max_findings: int) -> None:
    """Pretty-print scan results to console."""

    # Score banner
    verdict_color = {
        "PASS": "\033[92m",
        "AT RISK": "\033[93m",
        "FAIL": "\033[91m",
        "CRITICAL FAIL": "\033[91m",
    }.get(result.verdict, "")

    click.echo(f"\n{BOLD}Score: {result.score}/100   "
               f"Verdict: {verdict_color}{result.verdict}{RESET}")

    # ACT tier estimate
    if result.act_estimate:
        act = result.act_estimate
        click.echo(f"\n{BOLD}ACT Tier Estimate:{RESET} "
                   f"{act.get('estimated_tier', '?')} "
                   f"({act.get('confidence', '?')} confidence)")
        if act.get("hear_required"):
            click.echo(f"  {SEVERITY_COLORS['HIGH']}⚠️  HEAR Required (CP.10){RESET}: "
                       "Designate a Human Ethical Agent of Record before deployment")
        if act.get("cp9_required"):
            click.echo(f"  {SEVERITY_COLORS['HIGH']}⚠️  CP.9 Required{RESET}: "
                       "Agent Replication Governance must be implemented")

    # Governance gaps
    if result.governance_gaps:
        click.echo(f"\n{BOLD}Governance Gaps ({len(result.governance_gaps)}):{RESET}")
        for gap in result.governance_gaps[:5]:
            click.echo(f"  • {gap[:100]}")

    # Risk formula
    rfc = result.risk_formula_components
    if rfc:
        click.echo(f"\n{BOLD}Risk Score:{RESET} "
                   f"CVSS~{rfc.get('cvss_proxy', '?')} + "
                   f"Pillar({rfc.get('pillar_score', '?')}) + "
                   f"AAF~{rfc.get('aaf_partial_estimate', '?')} = "
                   f"{BOLD}{rfc.get('combined_risk_score', '?')}{RESET}")

    # Findings
    if result.violations:
        click.echo(f"\n{BOLD}Findings ({len(result.violations)} total):{RESET}")

        sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_v = sorted(result.violations, key=lambda v: sev_order.get(v.severity, 4))

        for i, v in enumerate(sorted_v[:max_findings]):
            sev_str = _color(f"[{v.severity}]", v.severity)
            ctrl = v.control_name or v.control_id
            click.echo(
                f"\n  {sev_str} {BOLD}{v.control_id}{RESET} {ctrl}"
            )
            click.echo(f"    File: {v.file_path}:{v.line_number}")
            click.echo(f"    Evidence: {v.evidence[:80]}")
            click.echo(f"    Fix: {v.remediation[:100]}")
            if v.compliance_frameworks:
                click.echo(f"    Frameworks: {', '.join(v.compliance_frameworks[:4])}")

        if len(result.violations) > max_findings:
            click.echo(f"\n  ... and {len(result.violations) - max_findings} more. "
                       "Run with --report json for full output.")

    else:
        click.echo(f"\n{BOLD}✅ No violations detected.{RESET}")

    # Pillar summary
    click.echo(f"\n{BOLD}Pillar Scores:{RESET}")
    pillar_names = {"P1": "Sanitize & Isolate", "P2": "Audit & Inventory",
                    "P3": "Fail-Safe & Recovery", "P4": "Engage & Monitor",
                    "P5": "Evolve & Educate", "CP": "Cross-Pillar"}
    for pid, pname in pillar_names.items():
        score = result.meta.get("pillar_scores", {}).get(pid, 100)
        bar_len = int(score / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        color = "\033[92m" if score >= 80 else "\033[93m" if score >= 60 else "\033[91m"
        click.echo(f"  {pid} {pname:<24} {color}{bar}{RESET} {score:.0f}")

    # Controls summary
    if result.controls_failed:
        click.echo(f"\n{BOLD}Controls Failed ({len(result.controls_failed)}):{RESET} "
                   f"{', '.join(result.controls_failed[:12])}"
                   f"{'...' if len(result.controls_failed) > 12 else ''}")


@cli.command()
@click.argument("report_path", type=click.Path(exists=True))
def show(report_path):
    """Display a previously generated compliance report in a readable format."""
    with open(report_path, encoding="utf-8") as f:
        data = json.load(f)

    click.echo(f"\n{BOLD}AI SAFE² v3.0 Compliance Report{RESET}")
    click.echo(f"Target:    {data.get('target', 'unknown')}")
    click.echo(f"Generated: {data.get('generated_at', 'unknown')}")
    click.echo(f"Score:     {data.get('summary', {}).get('score', '?')}/100")
    click.echo(f"Verdict:   {data.get('summary', {}).get('verdict', '?')}")

    fw = data.get("compliance_summary", {})
    click.echo(f"\nFrameworks Passing: {fw.get('frameworks_passing', '?')} / {fw.get('total_frameworks', 32)}")
    click.echo(f"Frameworks Failing: {fw.get('frameworks_failing', '?')}")


if __name__ == "__main__":
    cli()
