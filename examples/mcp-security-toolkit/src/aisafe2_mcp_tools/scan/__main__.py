"""mcp-scan CLI entry point."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import click
from aisafe2_mcp_tools.scan.analyzer import MCPScanner
from aisafe2_mcp_tools.scan.findings import SEVERITY_ORDER


@click.group(invoke_without_command=True)
@click.pass_context
@click.argument("target_path", required=False, default=".")
@click.option("--output", "-o", type=click.Choice(["terminal", "json", "html"]), default="terminal")
@click.option("--severity", "-s",
              type=click.Choice(["critical", "high", "medium", "low", "all"]), default="all")
@click.option("--ci", is_flag=True, help="Exit 1 if any critical or high findings")
def cli(ctx, target_path, output, severity, ci):
    """
    mcp-scan — AI SAFE2 v3.0 CP.5.MCP Static Code Analysis

    Scans MCP server source code across all threat classes from the
    CSI MCP Threat Intelligence Report (April 2026).

    \b
    Examples:
      mcp-scan .
      mcp-scan /path/to/server --output json > report.json
      mcp-scan . --output html > report.html
      mcp-scan . --severity critical --ci
      mcp-scan fix --interactive
    """
    if ctx.invoked_subcommand is not None:
        return

    target = Path(target_path).resolve()
    if not target.exists():
        click.echo(f"Error: {target} does not exist", err=True)
        sys.exit(1)

    scanner = MCPScanner(str(target))
    findings = scanner.scan()

    # Filter by severity
    if severity != "all":
        min_rank = SEVERITY_ORDER[severity]
        findings = [f for f in findings if SEVERITY_ORDER.get(f.severity, 0) >= min_rank]

    if output == "json":
        click.echo(scanner.json_report(findings))
    elif output == "html":
        click.echo(scanner.html_report(findings))
    else:
        click.echo(scanner.terminal_report(findings))

    if ci and any(f.severity in ("critical", "high") for f in findings):
        sys.exit(1)


@cli.command()
@click.argument("target_path", required=False, default=".")
@click.option("--interactive", "-i", is_flag=True, help="Step through fixes interactively")
@click.option("--auto", is_flag=True, help="Apply safe auto-fixes (HIGH and below only)")
def fix(target_path, interactive, auto):
    """
    Step through fix guidance for detected findings.

    CRITICAL findings require manual review and are never auto-fixed.
    See scan/fixes/*.template for code patterns.
    """
    target = Path(target_path).resolve()
    scanner = MCPScanner(str(target))
    findings = scanner.scan()

    critical = [f for f in findings if f.severity == "critical"]
    fixable = [f for f in findings if f.auto_fixable]

    if critical:
        click.echo(f"\n🔴 {len(critical)} CRITICAL finding(s) — manual review required:\n")
        for f in critical:
            click.echo(f"  [{f.finding_id}] {f.file}:{f.line} — {f.title}")
            click.echo(f"  Fix: {f.remediation[:120]}")
            if f.cve_refs:
                click.echo(f"  CVEs: {', '.join(f.cve_refs)}")
            click.echo()

    if not fixable:
        click.echo("No auto-fixable findings (after critical exclusion).")
        return

    click.echo(f"\n🟠 {len(fixable)} auto-fixable finding(s):\n")
    for finding in fixable:
        click.echo(f"  [{finding.finding_id}] {finding.file}:{finding.line}")
        click.echo(f"  {finding.title}")
        click.echo(f"  Fix: {finding.remediation[:120]}")
        if interactive:
            if not click.confirm("  Apply guidance?", default=True):
                continue
        elif not auto:
            click.echo("  (Use --interactive or --auto to apply)")
            continue
        click.echo(f"  ✓ Review {finding.file} at line {finding.line}")
        click.echo()


if __name__ == "__main__":
    cli()
