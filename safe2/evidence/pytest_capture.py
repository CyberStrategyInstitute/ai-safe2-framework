"""Associate a local pytest invocation with a fresh, bounded JUnit artifact."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from safe2.challenge.integrity import canonical_bytes
from safe2.challenge.io import read_bytes, safe_path
from safe2.contracts import validate_artifact
from safe2.evidence.junit import import_junit
from safe2.evidence.process_capture import capture_process
from safe2.evidence.test_result import evaluate_test_report
from safe2.evidence.tool_result import evaluate_tool_report


def verify_pytest_capture(capture: dict[str, Any]) -> dict[str, Any]:
    """Recompute internal consistency, not authenticity or actual execution."""
    def result(consistent: bool, reason: str, claim: dict[str, str] | None = None) -> dict[str, Any]:
        return {"internally_consistent": consistent, "reason": reason,
                "all_tests_passed_claim": claim, "execution_verified": False,
                "completion_verified": False, "conformance_claim": False}

    try:
        if validate_artifact("pytest-capture-v1", capture):
            return result(False, "capture_invalid")
        process, tests = capture["process_report"], capture["test_report"]
        for report, digest in ((process, capture["process_sha256"]),
                               (tests, capture["test_report_sha256"])):
            expected = hashlib.sha256(canonical_bytes(report)).hexdigest() if report is not None else None
            if digest != expected:
                return result(False, "capture_digest_mismatch")
        observation = process.get("process_observation")
        if observation is None or process["tool"] != "pytest":
            return result(False, "capture_process_missing_or_wrong_tool")
        _, process_reason, _ = evaluate_tool_report(canonical_bytes(process),
            task_id=process["task_id"], revision=process["revision"], environment=process["environment"],
            call_id=process["call_id"], tool="pytest", claimed_outcome="succeeded")
        if process_reason in {"tool_report_invalid", "tool_report_inconsistent_observation"}:
            return result(False, "capture_process_inconsistent")
        status, reason = "unverifiable", "process_capture_incomplete"
        if observation["capture_status"] == "completed":
            reason = "fresh_junit_missing_or_invalid"
            if tests is not None:
                if (tests["exit_code"] != observation["process_exit_code"] or
                        any(tests[key] != process[key] for key in ("task_id", "revision", "environment")) or
                        tests.get("import_provenance", {}).get("format") != "junit-xml"):
                    return result(False, "capture_report_binding_mismatch")
                status, reason, _ = evaluate_test_report(canonical_bytes(tests),
                    task_id=process["task_id"], revision=process["revision"], environment=process["environment"])
        elif tests is not None:
            return result(False, "capture_incomplete_process_has_report")
        claim = {"status": status, "reason": reason}
        if claim != capture["all_tests_passed_claim"]:
            return result(False, "capture_claim_mismatch", claim)
        return result(True, "capture_internally_consistent", claim)
    except (TypeError, ValueError, RecursionError):
        return result(False, "capture_invalid")


def capture_pytest(*, python: Path, cwd: Path, targets: tuple[str, ...], task_id: str,
                   revision: str, environment: str, call_id: str, timeout: int = 60) -> dict[str, Any]:
    """Run operator-selected tests; no signer key is loaded, no sandbox is claimed."""
    root = safe_path(cwd)
    if not root.is_dir() or not targets or len(targets) > 32:
        raise ValueError("Select 1..32 existing test files/directories under the working directory")
    selected = []
    for target in targets:
        path = safe_path(root / target)
        if not path.is_relative_to(root) or not path.exists():
            raise ValueError("Test selection must stay within the working directory")
        selected.append(str(path))
    # Only collector-owned temporary content is removed by this context manager.
    # The child remains same-user and can tamper with its own report: not an attestation.
    with tempfile.TemporaryDirectory(prefix="safe2-pytest-") as temporary:
        junit_path = Path(temporary) / "results.xml"
        command = (str(python), "-I", "-m", "pytest", "-q", *selected, f"--junitxml={junit_path}")
        process = capture_process(command, cwd=root, task_id=task_id, revision=revision,
                                  environment=environment, call_id=call_id, tool="pytest", timeout=timeout)
        observation = process["process_observation"]
        normalized = None
        status, reason = "unverifiable", "process_capture_incomplete"
        if observation["capture_status"] == "completed" and observation["output_complete"]:
            try:
                payload = read_bytes(junit_path, limit=1_000_000)
                normalized = import_junit(payload, task_id=task_id, revision=revision,
                                          environment=environment, exit_code=observation["process_exit_code"])
                status, reason, _ = evaluate_test_report(json.dumps(normalized).encode(),
                    task_id=task_id, revision=revision, environment=environment)
            except (OSError, TypeError, ValueError, RecursionError):
                status, reason = "unverifiable", "fresh_junit_missing_or_invalid"
    capture = {
        "schema_version": "safe2.pytest-capture.v1", "process_report": process,
        "process_sha256": hashlib.sha256(canonical_bytes(process)).hexdigest(),
        "test_report": normalized, "test_report_sha256": (
            hashlib.sha256(canonical_bytes(normalized)).hexdigest() if normalized is not None else None),
        "all_tests_passed_claim": {"status": status, "reason": reason},
        "association": "collector_selected_fresh_junit_path",
        "raw_junit_retained": False, "completion_verified": False, "conformance_claim": False,
        "limitations": [
            "Fresh report association reduces accidental stale pairing, not malicious same-user tampering.",
            "Revision/environment labels are declarations; dependencies and source contents are not snapshotted.",
            "No filesystem, network, descendant-process isolation, or trusted execution attestation is provided.",
            "Raw JUnit is discarded after normalization; only source hashes and normalized counts remain.",
        ],
    }
    if validate_artifact("pytest-capture-v1", capture):
        raise ValueError("Invalid pytest capture")
    return capture
