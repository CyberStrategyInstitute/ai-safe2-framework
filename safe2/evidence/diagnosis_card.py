"""Human-readable failure-localization card with escaped attributed text."""

from __future__ import annotations

from typing import Any


def _text(value: object) -> str:
    return (
        str(value)
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render(diagnosis: dict[str, Any]) -> str:
    """Render a compact decision-support card without upgrading evidence claims."""
    lines = [
        "# SAFE2 Failure Localization Card", "",
        f"- **Failure:** `{_text(diagnosis['source']['failure_id'])}`",
        f"- **Task:** `{_text(diagnosis['task']['task_id'])}`",
        f"- **Outcome:** `{_text(diagnosis['outcome']['status'])}` — {_text(diagnosis['outcome']['summary'])}",
        f"- **Diagnosis status:** `{_text(diagnosis['diagnosis_status'])}`",
        "- **Root cause verified:** `false`", "- **Probability estimate:** `false`", "",
        "## Evidence inventory", "",
        f"- Observed: {diagnosis['evidence_summary']['observed']}",
        f"- Declared: {diagnosis['evidence_summary']['declared']}",
        f"- Missing: {diagnosis['evidence_summary']['missing']}",
        f"- Distinct attributed sources: {diagnosis['evidence_summary']['distinct_attributed_sources']}", "",
        "## Ranked candidates", "",
    ]
    for candidate in diagnosis["candidates"]:
        location = candidate["location"]
        boundary = location["primary_category"]
        if location["interacting_category"]:
            boundary += f" → {location['interacting_category']}"
        lines.extend([
            f"### {candidate['rank']}. {_text(candidate['candidate_id'])}", "",
            f"- **Location:** `{_text(boundary)}`",
            f"- **Mode:** `{_text(candidate['failure_mode'])}`",
            f"- **Evidence level:** `{_text(candidate['evidence_assessment']['level'])}`",
            f"- **Repair owner:** `{_text(candidate['repair_owner'])}`",
            f"- **Explanation:** {_text(candidate['description'])}",
            f"- **Recommended action:** {_text(candidate['recommended_action'])}",
            "- **Supporting observations:** " + (
                ", ".join(f"`{_text(item)}`" for item in candidate["supporting_observation_ids"]) or "None"
            ),
            "- **Contradicting observations:** " + (
                ", ".join(f"`{_text(item)}`" for item in candidate["contradicting_observation_ids"]) or "None"
            ),
            "- **Assumptions:** " + (
                "; ".join(_text(item) for item in candidate["assumptions"]) or "None"
            ), "",
        ])
    lines.extend(["## Recommended next steps", ""])
    lines.extend(f"- {_text(item)}" for item in diagnosis["recommendations"])
    lines.extend([
        "", "## Evidence boundary", "",
        "This card ranks attributed candidate explanations. It does not verify root cause, provide a probability estimate, or claim AI SAFE2 conformance.", "",
    ])
    return "\n".join(lines)
