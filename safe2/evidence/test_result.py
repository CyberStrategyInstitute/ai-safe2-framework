"""Conservative interpretation of imported test reports, without executing tests."""

from __future__ import annotations

from typing import Any

from safe2.challenge.io import parse_json
from safe2.contracts import validate_artifact


def evaluate_test_report(
    payload: bytes, *, task_id: str, revision: str, environment: str,
) -> tuple[str, str, dict[str, Any] | None]:
    """Evaluate the narrow assertion 'this report records all tests passing'.

    Validating a supplied report cannot authenticate its author or test execution.
    Binding mismatches mean evidence is inapplicable, not that the task failed.
    Raw report text and untrusted identifiers are not copied into explanations.
    """
    try:
        report = parse_json(payload)
        if validate_artifact("test-result-v1", report):
            return "unverifiable", "test_report_invalid", None
    except (TypeError, ValueError, RecursionError):
        return "unverifiable", "test_report_invalid", None
    if (report["task_id"], report["revision"], report["environment"]) != (
        task_id, revision, environment,
    ):
        return "unverifiable", "test_report_binding_mismatch", None
    counts = report["counts"]
    if counts["total"] != sum(counts[key] for key in ("passed", "failed", "errors", "skipped")):
        return "unverifiable", "test_report_inconsistent_counts", None
    summary = {"counts": counts, "exit_code": report["exit_code"],
               "evidence_basis": "imported_report_not_authenticated_execution"}
    if counts["failed"] or counts["errors"] or report["exit_code"]:
        return "contradicted", "test_report_records_failure", summary
    if not counts["total"]:
        return "unverifiable", "test_report_no_tests", summary
    if counts["skipped"]:
        return "unverifiable", "test_report_has_skips", summary
    return "supported", "test_report_records_all_passed", summary
