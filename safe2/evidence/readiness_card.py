"""Human-readable release-readiness card with escaped untrusted text."""
from __future__ import annotations

from typing import Any


def _t(value: object) -> str:
    return str(value).replace("\r", " ").replace("\n", " ").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|")


def render(value: dict[str, Any]) -> str:
    gate = value["gate"]
    lines = ["# SAFE2 Release-Readiness Card", "", f"**{_t(value['target']['name'])} {_t(value['target']['version'])}** · `{_t(value['target']['revision'])}`", "", f"## Status: `{_t(gate['status'])}`", "", _t(value["recommendation"]), "", "- Release authorized: `false`", "- Conformance claim: `false`", f"- Decision owner: `{_t(value['decision_owner']['owner_id'])}` — {_t(value['decision_owner']['role'])}", "", "## Why", ""]
    lines.extend(f"- {_t(item)}" for item in (gate["reasons"] or ["No technical blocking condition was identified in supplied evidence."]))
    lines += ["", "## Evidence gaps", ""]
    lines.extend(f"- {_t(item)}" for item in (gate["gaps"] or ["None declared by this synthesis."]))
    lines += ["", "## Before and after", "", "| Inherited | Introduced | Changed | Resolved | Unknown |", "| ---: | ---: | ---: | ---: | ---: |", "| {inherited} | {introduced} | {changed} | {resolved} | {unknown} |".format(**value["change_summary"]), "", "## Required checks", "", f"- Required: {value['checks']['required']}", f"- Missing: {len(value['checks']['missing'])}", f"- Failed/cancelled: {len(value['checks']['failed'])}", f"- Pending/unavailable: {len(value['checks']['incomplete'])}", "", "## Residual risks", ""]
    if value["residual_risks"]:
        lines += ["| Severity | Risk | Disposition | Owner | Action |", "| --- | --- | --- | --- | --- |"]
        lines.extend(f"| {_t(r['severity'])} | {_t(r['title'])} | {_t(r['disposition'])} | {_t(r['owner_id'])} | {_t(r['action'])} |" for r in value["residual_risks"])
    else: lines.append("No residual risks were supplied; this is not proof that none exist.")
    lines += ["", "## Paths forward", ""]
    lines.extend(f"- **{_t(a['priority'])}:** {_t(a['description'])} — `{_t(a['owner_id'])}`" for a in value["actions"])
    lines += ["", "## Rollback", "", f"- Available: `{str(value['rollback']['available']).lower()}`", f"- Procedure: {_t(value['rollback']['procedure'])}", "", "## Evidence boundary", "", "This card synthesizes supplied technical evidence. It does not authorize release, authenticate claims, prove execution or safety, or establish AI SAFE² conformance.", ""]
    return "\n".join(lines)
