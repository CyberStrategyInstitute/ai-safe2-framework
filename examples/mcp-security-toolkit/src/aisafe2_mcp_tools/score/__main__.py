"""
AI SAFE2 MCP Security Toolkit — mcp-score CLI
Remote black-box CP.5.MCP scoring for any MCP HTTP server.

Usage:
  mcp-score https://your-mcp-server.example/mcp
  mcp-score https://example.com/mcp --token your-token --output html > report.html
  mcp-score https://example.com/mcp --output json > report.json
  mcp-score --batch servers.txt --output json > batch-report.json
  mcp-score https://example.com/mcp --badge
  mcp-score https://example.com/mcp --controls MCP-2,MCP-6,MCP-7

Authorization notice:
  By using this tool, you attest that you are authorized to assess the target
  server. mcp-score reads only publicly accessible endpoints and does not
  modify server state.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click

from aisafe2_mcp_tools.score.assessor import MCPAssessor
from aisafe2_mcp_tools.score.badge import generate_badge_report_section, generate_badge_markdown
from aisafe2_mcp_tools.score.reporter import print_terminal_report, to_json, to_html


@click.group(invoke_without_command=True)
@click.pass_context
@click.argument("server_url", required=False)
@click.option("--token", "-t", default=None, help="Bearer token for authenticated servers")
@click.option(
    "--output", "-o",
    type=click.Choice(["terminal", "json", "html"]),
    default="terminal",
    help="Output format",
)
@click.option("--badge", is_flag=True, help="Show full badge implementation guide")
@click.option("--batch", type=click.Path(exists=True), default=None,
              help="Path to file with one server URL per line")
@click.option("--timeout", default=15.0, help="Per-request timeout in seconds")
@click.option("--ci-fail-below", default=0, type=int,
              help="Exit code 1 if score is below this threshold (for CI gates)")
def cli(ctx, server_url, token, output, badge, batch, timeout, ci_fail_below):
    """
    mcp-score — AI SAFE2 v3.0 CP.5.MCP Remote Security Assessment

    Score any MCP HTTP server against the AI SAFE2 CP.5.MCP control profile.
    Servers scoring 70+ are eligible for the AI SAFE2 MCP badge.

    \b
    Examples:
      mcp-score https://example.com/mcp
      mcp-score https://example.com/mcp --token pro_xyz --output html > report.html
      mcp-score --batch servers.txt --output json
      mcp-score https://example.com/mcp --badge
      mcp-score https://example.com/mcp --ci-fail-below 70
    """
    if ctx.invoked_subcommand is not None:
        return

    if batch:
        asyncio.run(_run_batch(batch, token, output, timeout, ci_fail_below))
        return

    if not server_url:
        click.echo(ctx.get_help())
        sys.exit(0)

    asyncio.run(_run_single(server_url, token, output, badge, timeout, ci_fail_below))


async def _run_single(server_url, token, output, show_badge, timeout, ci_fail_below):
    assessor = MCPAssessor(server_url, token=token, timeout=timeout)
    report = await assessor.assess()

    if output == "terminal":
        print_terminal_report(report)
        if show_badge:
            click.echo("\n" + "=" * 60)
            click.echo(generate_badge_report_section(report))
    elif output == "json":
        click.echo(to_json(report))
    elif output == "html":
        click.echo(to_html(report))

    if ci_fail_below > 0 and report.total_score < ci_fail_below:
        sys.exit(1)


async def _run_batch(batch_file, token, output, timeout, ci_fail_below):
    urls = [
        line.strip()
        for line in Path(batch_file).read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    if not urls:
        click.echo("No URLs found in batch file", err=True)
        sys.exit(1)

    click.echo(f"Assessing {len(urls)} servers...", err=True)
    reports = []
    for url in urls:
        click.echo(f"  Scanning {url}...", err=True)
        assessor = MCPAssessor(url, token=token, timeout=timeout)
        report = await assessor.assess()
        reports.append(report)
        click.echo(f"  → Score: {report.total_score}/100 ({report.rating})", err=True)

    if output == "json":
        import json
        from aisafe2_mcp_tools.score.reporter import to_json
        batch_result = {
            "schema": "aisafe2-mcp-score-batch-v1",
            "server_count": len(reports),
            "eligible_count": sum(1 for r in reports if r.badge_eligible),
            "average_score": round(sum(r.total_score for r in reports) / len(reports), 1),
            "reports": [json.loads(to_json(r)) for r in reports],
        }
        click.echo(json.dumps(batch_result, indent=2))
    else:
        for report in reports:
            print_terminal_report(report)

    if ci_fail_below > 0:
        failing = [r for r in reports if r.total_score < ci_fail_below]
        if failing:
            click.echo(
                f"\n{len(failing)} server(s) scored below {ci_fail_below}: "
                + ", ".join(r.server_url for r in failing),
                err=True,
            )
            sys.exit(1)


if __name__ == "__main__":
    cli()
