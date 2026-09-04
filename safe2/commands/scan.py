"""`safe2 scan` - static, informational scanning. No pass/fail decision.

For CI gating use `safe2 gate`, which runs the same engines and turns the
result into an exit code. `scan` is for a human looking at what's there.
"""
from __future__ import annotations

from pathlib import Path

import click

from safe2.engines import project as project_engine
from safe2.engines import skill_gate
from safe2.reporting.formats import print_project_findings, print_skill_findings

BOLD = "\033[1m"
RESET = "\033[0m"


@click.group()
def scan():
    """Static analysis - report findings, make no pass/fail decision."""


@scan.command("project")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--controls-json", default=None, help="Path to ai-safe2-controls-v3.0.json (auto-detected if omitted)")
@click.option("--max-findings", default=50, help="Maximum findings to display (default: 50)")
@click.option("--max-files", default=10_000, type=click.IntRange(min=1), show_default=True)
def scan_project(path, controls_json, max_findings, max_files):
    """Scan a codebase against the 161 AI SAFE2 v3.0 controls."""
    click.echo(f"\n{BOLD}AI SAFE2 v3.0 Project Scan{RESET}\nTarget: {path}\n" + "-" * 60)
    result = project_engine.run_scan(path, controls_json=controls_json, max_files=max_files)
    print_project_findings(result, max_findings=max_findings)


@scan.command("skill")
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False))
def scan_skill(path):
    """Scan a skill package directory for trust-gate violations (no decision)."""
    root = Path(path)
    findings = skill_gate.scan(root)
    print_skill_findings(root, findings)


@scan.command("mcp")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--severity", "-s", type=click.Choice(["critical", "high", "medium", "low", "all"]), default="all")
@click.option("--output", "-o", type=click.Choice(["terminal", "json", "html"]), default="terminal")
def scan_mcp(path, severity, output):
    """Static-analyze MCP server source code (CP.5.MCP threat classes)."""
    from aisafe2_mcp_tools.scan.analyzer import MCPScanner
    from aisafe2_mcp_tools.scan.findings import SEVERITY_ORDER

    target = Path(path).resolve()
    scanner = MCPScanner(str(target))
    findings = scanner.scan()

    if severity != "all":
        min_rank = SEVERITY_ORDER[severity]
        findings = [f for f in findings if SEVERITY_ORDER.get(f.severity, 0) >= min_rank]

    if output == "json":
        click.echo(scanner.json_report(findings))
    elif output == "html":
        click.echo(scanner.html_report(findings))
    else:
        click.echo(scanner.terminal_report(findings))
