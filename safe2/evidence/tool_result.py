"""Check a tool-outcome claim against a bound, untrusted imported report."""

from __future__ import annotations

from typing import Any

from safe2.challenge.io import parse_json
from safe2.contracts import validate_artifact


def evaluate_tool_report(
    payload: bytes, *, task_id: str, revision: str, environment: str,
    call_id: str, tool: str, claimed_outcome: str,
) -> tuple[str, str, dict[str, Any] | None]:
    """Do not equate unknown or missing evidence with a false claim.

    A reported unavailable tool can support an accurately disclosed blocker, not
    successful task completion. A successful call does not prove useful results.
    """
    try:
        report = parse_json(payload)
        if validate_artifact("tool-result-v1", report):
            return "unverifiable", "tool_report_invalid", None
    except (TypeError, ValueError, RecursionError):
        return "unverifiable", "tool_report_invalid", None
    if (report["task_id"], report["revision"], report["environment"],
            report["call_id"], report["tool"]) != (task_id, revision, environment, call_id, tool):
        return "unverifiable", "tool_report_binding_mismatch", None
    observation = report.get("process_observation")
    if observation is not None:
        state = observation["capture_status"]
        code = observation["process_exit_code"]
        expected = {
            "completed": "succeeded" if code == 0 else "failed",
            "launch_unavailable": "unavailable", "launch_failed": "failed",
            "timeout": "failed", "output_limit": "unknown", "drain_incomplete": "unknown",
        }[state]
        complete = observation["output_complete"]
        hashes_present = all(observation[key] is not None for key in ("stdout_sha256", "stderr_sha256"))
        if (expected != report["outcome"] or (state == "completed" and
                (code is None or not complete or not hashes_present))
                or (state != "completed" and complete)):
            return "unverifiable", "tool_report_inconsistent_observation", None
    summary = {
        "claimed_outcome": claimed_outcome, "reported_outcome": report["outcome"],
        "evidence_basis": "imported_report_not_authenticated_execution",
    }
    if report["outcome"] == "unknown":
        return "unverifiable", "tool_report_unknown_outcome", summary
    if report["outcome"] != claimed_outcome:
        return "contradicted", "tool_report_conflicts_with_claim", summary
    return "supported", "tool_report_matches_claim", summary
