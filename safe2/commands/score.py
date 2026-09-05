"""`safe2 score` - the number, without a full findings dump or a pass/fail exit code.

Use `scan` for full findings, `gate` for CI pass/fail. `score` is the quick
"where do we stand" check - this is also what feeds the AISM benchmark
scoring pass (PART 3, AISM family): running `safe2 score project` against
each platform's runtime package is the intended way to produce the
benchmark's raw numbers.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import click

from safe2.engines import project as project_engine
from safe2.reporting.formats import print_project_summary


@click.group()
def score():
    """Numeric scores only - no findings dump, no exit-code gating."""


@score.command("project")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--controls-json", default=None)
def score_project(path, controls_json):
    """Score a codebase against the 161 AI SAFE2 v3.0 controls."""
    result = project_engine.run_scan(path, controls_json=controls_json)
    print_project_summary(result)


@score.command("mcp")
@click.argument("server_url", required=False)
@click.option("--token", "-t", default=None)
@click.option("--batch", type=click.Path(exists=True), default=None, help="File with one server URL per line")
@click.option("--badge", is_flag=True, help="Show the badge implementation guide")
@click.option("--timeout", default=15.0)
@click.pass_context
def score_mcp(ctx, server_url, token, batch, badge, timeout):
    """Remote black-box score an MCP HTTP server (or a batch of them)."""
    from aisafe2_mcp_tools.score.assessor import MCPAssessor
    from aisafe2_mcp_tools.score.badge import generate_badge_report_section
    from aisafe2_mcp_tools.score.reporter import print_terminal_report

    if batch:
        asyncio.run(_score_batch(batch, token, timeout))
        return

    if not server_url:
        click.echo(ctx.get_help())
        return

    async def _run():
        try:
            assessor = MCPAssessor(server_url, token=token, timeout=timeout)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        report = await assessor.assess()
        print_terminal_report(report)
        if badge:
            click.echo("\n" + "=" * 60)
            click.echo(generate_badge_report_section(report))

    asyncio.run(_run())


async def _score_batch(batch_file, token, timeout):
    from aisafe2_mcp_tools.score.assessor import MCPAssessor
    from aisafe2_mcp_tools.score.reporter import print_terminal_report

    path = Path(batch_file)
    if path.is_symlink() or path.stat().st_size > 1_000_000:
        raise click.ClickException("batch file must be a regular file no larger than 1 MB")
    urls = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]
    if not urls:
        click.echo("No URLs found in batch file", err=True)
        return
    if len(urls) > 1_000:
        raise click.ClickException("batch file contains more than 1,000 targets")

    # Validate the complete batch before any network request occurs.
    try:
        assessors = [MCPAssessor(url, token=token, timeout=timeout) for url in urls]
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    for url, assessor in zip(urls, assessors, strict=True):
        click.echo(f"Scoring {url}...", err=True)
        report = await assessor.assess()
        print_terminal_report(report)
