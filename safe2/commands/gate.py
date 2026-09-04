"""`safe2 gate` - the pass/fail decision layer for CI/CD.

Exit-code contract (uniform across every `gate` subcommand):
  0 = PASS / APPROVE     — safe to proceed
  1 = FAIL / REJECT      — block the pipeline
  2 = HOLD FOR REVIEW    — needs a human; only emitted by `gate skill` in
                            non-strict mode (a HIGH-severity finding without
                            a CRITICAL one). Treat as a soft fail in CI: it
                            should not auto-merge, but it's not an
                            automatic hard reject either.
  3 = ERROR               — bad input (target missing, unreachable, etc.),
                            not a security verdict.

`gate project` and `gate mcp` have no HOLD state today and only ever
return 0/1/3; `gate skill` is the only one that can return 2. This is
documented here once so all three subcommands, and anyone scripting
against them, share one contract instead of the three inconsistent ones
the pre-consolidation tools had (skill_trust_gate.py returned 0/2 only;
mcp-scan --ci and mcp-score --ci-fail-below both used bare 0/1).
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from urllib.parse import urlparse

import click

from safe2.engines import project as project_engine
from safe2.engines import skill_gate
from safe2.reporting.formats import print_project_findings, print_skill_findings

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_HOLD = 2
EXIT_ERROR = 3


@click.group()
def gate():
    """Pass/fail CI gates. See module docstring for the exit-code contract."""


@gate.command("project")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--tier", default="Tier1", type=click.Choice(["Tier1", "Tier2", "Tier3"]),
              help="Tier3=strict (fail <90), Tier2=balanced (fail <70), Tier1=baseline (fail <50)")
@click.option("--fail-under", default=None, type=float, help="Overrides --tier with an explicit score threshold")
@click.option("--controls-json", default=None)
@click.option("--quiet", is_flag=True)
def gate_project(path, tier, fail_under, controls_json, quiet):
    """Gate a codebase on its 161-control score."""
    result = project_engine.run_scan(path, controls_json=controls_json)
    if not quiet:
        print_project_findings(result)

    if project_engine.fails(result, tier, fail_under):
        reason = "scan was truncated" if result.meta.get("scan_truncated") else "score below threshold"
        click.echo(f"\nGATE: FAIL - {reason} ({result.score}/100)", err=True)
        sys.exit(EXIT_FAIL)
    click.echo(f"\nGATE: PASS - score {result.score}/100")
    sys.exit(EXIT_PASS)


@gate.command("skill")
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False))
@click.option("--strict", is_flag=True, help="Treat HIGH severity as REJECT instead of HOLD FOR REVIEW")
@click.option("--quiet", is_flag=True)
def gate_skill(path, strict, quiet):
    """Gate a skill package on the static trust-gate rules."""
    root = Path(path)
    findings = skill_gate.scan(root)
    decision, severity = skill_gate.decision_for(findings, strict)

    if not quiet:
        print_skill_findings(root, findings)
    click.echo(f"\nGATE: {decision} (highest severity: {severity})")
    sys.exit(skill_gate.DECISION_EXIT_CODES[decision])


@gate.command("mcp")
@click.argument("target")
@click.option("--ci-fail-below", default=70, type=int, help="For a URL target: fail if the remote score is below this")
@click.option("--token", default=None, help="Bearer token, for a URL target")
@click.option("--timeout", default=15.0, help="Per-request timeout in seconds, for a URL target")
def gate_mcp(target, ci_fail_below, token, timeout):
    """Gate an MCP target - a URL is remotely scored, a path is statically scanned."""
    if urlparse(target).scheme in ("http", "https"):
        from aisafe2_mcp_tools.score.assessor import MCPAssessor
        from aisafe2_mcp_tools.score.reporter import print_terminal_report

        assessor = MCPAssessor(target, token=token, timeout=timeout)
        report = asyncio.run(assessor.assess())
        print_terminal_report(report)
        if report.total_score < ci_fail_below:
            click.echo(f"\nGATE: FAIL - {report.total_score}/100 below {ci_fail_below}", err=True)
            sys.exit(EXIT_FAIL)
        click.echo(f"\nGATE: PASS - {report.total_score}/100")
        sys.exit(EXIT_PASS)

    from aisafe2_mcp_tools.scan.analyzer import MCPScanner

    path = Path(target).resolve()
    if not path.exists():
        click.echo(f"GATE: ERROR - {path} does not exist", err=True)
        sys.exit(EXIT_ERROR)

    scanner = MCPScanner(str(path))
    findings = scanner.scan()
    click.echo(scanner.terminal_report(findings))
    if any(f.severity in ("critical", "high") for f in findings):
        click.echo("\nGATE: FAIL - critical/high findings present", err=True)
        sys.exit(EXIT_FAIL)
    click.echo("\nGATE: PASS - no critical/high findings")
    sys.exit(EXIT_PASS)
