"""`safe2 report` - run an engine and emit a compliance artifact in a chosen format.

This is the one place that knows how to turn a result into json / sarif /
markdown / html, instead of that logic being scattered across
ISO42001Report, three different aisafe2_mcp_tools reporter modules, and
skill_trust_gate.py's ad hoc writer. Each `report` subcommand still calls
the real engine and its real native serializer where one exists (SARIF for
project, JSON/HTML for the two MCP tools) — this module adds markdown,
which none of the four originals produced, and a single consistent
--format/--output surface on top.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import click

from safe2.engines import project as project_engine
from safe2.engines import skill_gate
from safe2.reporting.formats import (
    mcp_scan_findings_to_markdown,
    mcp_score_report_to_markdown,
    project_result_to_markdown,
    skill_findings_to_markdown,
)


@click.group()
def report():
    """Generate a compliance artifact (json / sarif / markdown / html) from a scan."""


@report.command("project")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--format", "fmt", type=click.Choice(["json", "sarif", "markdown", "all"]), default="json")
@click.option("--output", default="ai_safe2_audit_report", help="Output path stem (extension added per format)")
@click.option("--controls-json", default=None)
def report_project(path, fmt, output, controls_json):
    result = project_engine.run_scan(path, controls_json=controls_json)
    stem = output

    if fmt in ("json", "all"):
        project_engine.ISO42001Report().generate_report(result, output_path=f"{stem}.json", include_sarif=False)
    if fmt in ("sarif", "all"):
        project_engine.ISO42001Report().generate_report(result, output_path=f"{stem}.json", include_sarif=True)
    if fmt in ("markdown", "all"):
        Path(f"{stem}.md").write_text(project_result_to_markdown(result, path), encoding="utf-8")
        click.echo(f"Markdown report: {stem}.md")


@report.command("skill")
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False))
@click.option("--format", "fmt", type=click.Choice(["json", "markdown", "all"]), default="all")
@click.option("--output", default="skill_trust_gate_report")
@click.option("--strict", is_flag=True)
def report_skill(path, fmt, output, strict):
    import json as _json

    root = Path(path)
    findings = skill_gate.scan(root)
    decision, severity = skill_gate.decision_for(findings, strict)

    if fmt in ("json", "all"):
        Path(f"{output}.json").write_text(
            _json.dumps(
                {
                    "scanner": "AI SAFE2 Skill Trust Gate",
                    "skill_path": root.as_posix(),
                    "decision": decision,
                    "severity": severity,
                    "findings": [f.as_dict() for f in findings],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        click.echo(f"JSON report: {output}.json")
    if fmt in ("markdown", "all"):
        Path(f"{output}.md").write_text(
            skill_findings_to_markdown(root, findings, decision, severity), encoding="utf-8"
        )
        click.echo(f"Markdown report: {output}.md")


@report.command("mcp-scan")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--format", "fmt", type=click.Choice(["json", "html", "markdown", "all"]), default="json")
@click.option("--output", default="mcp_scan_report")
def report_mcp_scan(path, fmt, output):
    from aisafe2_mcp_tools.scan.analyzer import MCPScanner

    target = Path(path).resolve()
    scanner = MCPScanner(str(target))
    findings = scanner.scan()

    if fmt in ("json", "all"):
        Path(f"{output}.json").write_text(scanner.json_report(findings), encoding="utf-8")
        click.echo(f"JSON report: {output}.json")
    if fmt in ("html", "all"):
        Path(f"{output}.html").write_text(scanner.html_report(findings), encoding="utf-8")
        click.echo(f"HTML report: {output}.html")
    if fmt in ("markdown", "all"):
        Path(f"{output}.md").write_text(mcp_scan_findings_to_markdown(findings, str(target)), encoding="utf-8")
        click.echo(f"Markdown report: {output}.md")


@report.command("mcp-score")
@click.argument("server_url")
@click.option("--format", "fmt", type=click.Choice(["json", "html", "markdown", "all"]), default="json")
@click.option("--output", default="mcp_score_report")
@click.option("--token", default=None)
@click.option("--timeout", default=15.0)
def report_mcp_score(server_url, fmt, output, token, timeout):
    from aisafe2_mcp_tools.score.assessor import MCPAssessor
    from aisafe2_mcp_tools.score.reporter import to_html, to_json

    async def _run():
        assessor = MCPAssessor(server_url, token=token, timeout=timeout)
        return await assessor.assess()

    result = asyncio.run(_run())

    if fmt in ("json", "all"):
        Path(f"{output}.json").write_text(to_json(result), encoding="utf-8")
        click.echo(f"JSON report: {output}.json")
    if fmt in ("html", "all"):
        Path(f"{output}.html").write_text(to_html(result), encoding="utf-8")
        click.echo(f"HTML report: {output}.html")
    if fmt in ("markdown", "all"):
        Path(f"{output}.md").write_text(mcp_score_report_to_markdown(result), encoding="utf-8")
        click.echo(f"Markdown report: {output}.md")
