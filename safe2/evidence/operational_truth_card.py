"""Human projection of canonical operational truth JSON."""

from __future__ import annotations

from typing import Any


def render(value: dict[str, Any]) -> str:
    task = value["task"]
    lines = ["# AI SAFE² operational truth card", "", f"Task: `{task['task_id']}`", f"Revision: `{task['revision']}`", f"Gate: **{value['gate']}**", f"Decision owner: `{value['decision_owner']}`", "", "## Completion", "", f"Assessment: `{value['completion']['assessment']}`. Completion verified: `false`.", "", "## Coverage", "", "| Domain | Status |", "|---|---|"]
    lines += [f"| {domain} | {status} |" for domain, status in sorted(value["coverage"].items())]
    lines += ["", "## Evidence gaps", ""] + ([f"- {item}" for item in value["gaps"]] or ["- None in supplied evidence."])
    lines += ["", "## Conflicts", ""] + ([f"- {item}" for item in value["conflicts"]] or ["- None in supplied evidence."])
    lines += ["", "## Usage", "", f"Unique event identifiers: {value['usage']['events']}. Duplicate ownership: {value['usage']['duplicate_ownership']}. Billing verified: `false`.", "", "## Limits", ""]
    lines += [f"- {item}" for item in value["limitations"]]
    return "\n".join(lines) + "\n"
