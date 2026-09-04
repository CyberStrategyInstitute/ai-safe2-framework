"""Shared console rendering + markdown fallback rendering.

Each absorbed engine already knows how to serialize its own native result
type to JSON/SARIF/HTML (ISO42001Report, aisafe2_mcp_tools' reporter
modules). This module holds only the bits that were duplicated across the
old scanner/cli.py, skill_trust_gate.py, and the mcp_tools CLIs: ANSI
color banners and a markdown writer for the one format none of the
original engines produced (project + mcp-scan markdown).
"""
from __future__ import annotations

import click

SEVERITY_COLORS = {
    "CRITICAL": "\033[91m",
    "HIGH": "\033[93m",
    "MEDIUM": "\033[94m",
    "LOW": "\033[92m",
    "INFO": "\033[0m",
}
RESET = "\033[0m"
BOLD = "\033[1m"

PILLAR_NAMES = {
    "P1": "Sanitize & Isolate",
    "P2": "Audit & Inventory",
    "P3": "Fail-Safe & Recovery",
    "P4": "Engage & Monitor",
    "P5": "Evolve & Educate",
    "CP": "Cross-Pillar",
}


def _console_text(value: object) -> str:
    """Render common typographic characters safely in legacy Windows consoles."""
    text = str(value)
    for source, replacement in (("\u2014", "-"), ("\u2013", "-"), ("\u2022", "*"), ("\u00b2", "2")):
        text = text.replace(source, replacement)
    return text


def color(text: str, severity: str) -> str:
    return f"{SEVERITY_COLORS.get(severity, '')}{text}{RESET}"


def print_project_summary(result, *, echo=click.echo) -> None:
    """Score + verdict + pillar bars only — no findings. Used by `safe2 score project`."""
    verdict_color = {
        "PASS": "\033[92m", "AT RISK": "\033[93m",
        "FAIL": "\033[91m", "CRITICAL FAIL": "\033[91m",
    }.get(result.verdict, "")
    echo(f"\n{BOLD}Score: {result.score}/100   Verdict: {verdict_color}{result.verdict}{RESET}")
    if result.meta.get("scan_truncated"):
        echo(
            f"WARNING: scan truncated at {result.meta.get('scanned_files')} files; "
            "the score is incomplete."
        )

    if result.act_estimate:
        act = result.act_estimate
        echo(f"{BOLD}ACT Tier Estimate:{RESET} {act.get('estimated_tier', '?')} "
             f"({act.get('confidence', '?')} confidence)")

    echo(f"\n{BOLD}Pillar Scores:{RESET}")
    for pid, pname in PILLAR_NAMES.items():
        score = result.meta.get("pillar_scores", {}).get(pid, 100)
        bar_len = int(score / 5)
        # ASCII is deliberate: agents and Windows CI frequently capture output
        # through consoles that cannot encode Unicode block characters.
        bar = "#" * bar_len + "." * (20 - bar_len)
        c = "\033[92m" if score >= 80 else "\033[93m" if score >= 60 else "\033[91m"
        echo(f"  {pid} {pname:<24} {c}{bar}{RESET} {score:.0f}")


def print_project_findings(result, max_findings: int = 50, *, echo=click.echo) -> None:
    """Full findings dump. Used by `safe2 scan project`."""
    print_project_summary(result, echo=echo)

    if result.governance_gaps:
        echo(f"\n{BOLD}Governance Gaps ({len(result.governance_gaps)}):{RESET}")
        for gap in result.governance_gaps[:5]:
            echo(f"  * {_console_text(gap[:100])}")

    if not result.violations:
        echo(f"\n{BOLD}No violations detected.{RESET}")
        return

    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    sorted_v = sorted(result.violations, key=lambda v: sev_order.get(v.severity, 4))
    echo(f"\n{BOLD}Findings ({len(result.violations)} total):{RESET}")
    for v in sorted_v[:max_findings]:
        echo(f"\n  {color('[' + v.severity + ']', v.severity)} {BOLD}{v.control_id}{RESET} "
             f"{_console_text(v.control_name or v.control_id)}")
        echo(f"    File: {_console_text(v.file_path)}:{v.line_number}")
        echo(f"    Evidence: {_console_text(v.evidence[:80])}")
        echo(f"    Fix: {_console_text(v.remediation[:100])}")
    if len(result.violations) > max_findings:
        echo(f"\n  ... and {len(result.violations) - max_findings} more. Use `safe2 report project` for full output.")


def print_skill_findings(root, findings, *, echo=click.echo) -> None:
    echo(f"\n{BOLD}Skill Trust Gate - {root}{RESET}")
    if not findings:
        echo(f"{color('No findings.', 'LOW')}")
        return
    for f in findings:
        echo(f"  {color('[' + f.severity + ']', f.severity)} {f.rule_id} "
             f"{_console_text(f.file)}:{f.line} - {_console_text(f.description)}")


def project_result_to_markdown(result, target: str) -> str:
    lines = [
        "# AI SAFE2 Project Scan Report",
        "",
        f"- Target: `{target}`",
        f"- Score: {result.score}/100",
        f"- Verdict: {result.verdict}",
        f"- Controls failed: {len(result.controls_failed)}",
        f"- Findings: {len(result.violations)}",
        "",
        "## Pillar Scores",
        "",
    ]
    for pid, pname in PILLAR_NAMES.items():
        score = result.meta.get("pillar_scores", {}).get(pid, 100)
        lines.append(f"- {pid} {pname}: {score:.0f}")
    lines += ["", "## Findings", ""]
    if result.violations:
        for v in result.violations:
            lines.append(
                f"- **{v.severity}** `{v.control_id}` {v.file_path}:{v.line_number} — "
                f"{v.evidence[:100]} (fix: {v.remediation[:120]})"
            )
    else:
        lines.append("No violations detected.")
    return "\n".join(lines) + "\n"


def skill_findings_to_markdown(root, findings, decision: str | None = None, severity: str | None = None) -> str:
    lines = ["# AI SAFE² Skill Trust Gate Report", ""]
    if decision:
        lines += [f"- Decision: {decision}", f"- Highest severity: {severity}"]
    lines += [f"- Skill path: `{root}`", "", "## Findings", ""]
    if findings:
        for f in findings:
            lines.append(f"- {f.severity} {f.rule_id}: {f.file}:{f.line} - {f.description}")
    else:
        lines.append("No static trust-gate findings.")
    return "\n".join(lines) + "\n"


def mcp_scan_findings_to_markdown(findings, target: str) -> str:
    lines = ["# AI SAFE2 MCP Static Scan Report", "", f"- Target: `{target}`", f"- Findings: {len(findings)}", "", "## Findings", ""]
    if findings:
        for f in findings:
            cve = f", CVEs: {', '.join(f.cve_refs)}" if getattr(f, "cve_refs", None) else ""
            lines.append(f"- **{f.severity.upper()}** `{f.finding_id}` {f.file}:{f.line} — {f.title}{cve}")
    else:
        lines.append("No findings.")
    return "\n".join(lines) + "\n"


def mcp_score_report_to_markdown(report) -> str:
    lines = [
        "# AI SAFE2 MCP Server Score Report",
        "",
        f"- Server: `{report.server_url}`",
        f"- Score: {report.total_score}/100",
        f"- Rating: {report.rating}",
        f"- Badge eligible: {report.badge_eligible}",
    ]
    return "\n".join(lines) + "\n"
