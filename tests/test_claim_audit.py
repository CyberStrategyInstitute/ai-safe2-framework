from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from click.testing import CliRunner

from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.evidence.claim_audit import build, render_markdown


def source() -> dict:
    return {
        "schema_version": "safe2.claim-audit-source.v1",
        "audit_id": "audit-1",
        "task_id": "task-1",
        "claims": [
            {"id": "done", "claim_type": "task_completion", "asserted_outcome": "completed", "evidence_criteria_ids": ["artifact"]},
            {"id": "search", "claim_type": "search_outcome", "asserted_outcome": "unavailable", "evidence_criteria_ids": ["search-call"]},
            {"id": "tests", "claim_type": "test_outcome", "asserted_outcome": "succeeded", "evidence_criteria_ids": ["tests"]},
        ],
    }


def receipt() -> dict:
    return {
        "schema_version": "safe2.task-receipt.v1",
        "task_id": "task-1", "parent_task_id": None, "harness": "codex", "observed_at": "2026-10-03T00:00:00Z",
        "input_sha256": "0" * 64, "verification_scope": "local_artifact_and_imported_report_consistency",
        "criteria": [
            {"id": "artifact", "kind": "artifact_sha256", "status": "supported", "reason": "digest_matches", "observed_sha256": "1" * 64},
            {"id": "search-call", "kind": "tool_report", "status": "supported", "authentication": "not_present", "reason": "tool_report_matches_claim", "tool_summary": {"claimed_outcome": "unavailable", "reported_outcome": "unavailable", "evidence_basis": "imported_report_not_authenticated_execution"}, "observed_sha256": "2" * 64},
            {"id": "tests", "kind": "test_report", "status": "contradicted", "authentication": "not_present", "reason": "test_report_records_failure", "test_summary": {"counts": {"total": 2, "passed": 1, "failed": 1, "errors": 0, "skipped": 0}, "exit_code": 1, "evidence_basis": "imported_report_not_authenticated_execution"}, "observed_sha256": "3" * 64},
        ],
        "counts": {"supported": 2, "contradicted": 1, "unverifiable": 0},
        "usage": [], "usage_verification": "unverified_source_declarations", "completion_verified": False, "conformance_claim": False,
        "limitations": ["fixture"],
    }


def encoded(value: dict) -> bytes:
    return json.dumps(value).encode("utf-8")


def test_audit_separates_consistency_contradiction_and_disclosure() -> None:
    result = build(encoded(source()), [encoded(receipt())])
    assert not validate_artifact("claim-audit-v1", result)
    assert result["summary"] == {"total": 3, "evidence_consistent": 2, "contradicted": 1, "unverifiable": 0, "explicit_limitation_disclosures": 1, "evidence_coverage_ratio": 0.666667, "contradiction_ratio": 0.333333}
    assert result["gate"] == "review_required"
    assert result["completion_verified"] is False
    assert result["deception_inferred"] is False
    assert "HONEST" not in render_markdown(result).upper()


def test_missing_duplicate_or_unverifiable_evidence_never_looks_clean() -> None:
    declared = source()
    declared["claims"] = [{"id": "missing", "claim_type": "task_completion", "asserted_outcome": "completed", "evidence_criteria_ids": ["absent"]}]
    result = build(encoded(declared), [encoded(receipt())])
    assert result["claims"][0]["status"] == "unverifiable"
    declared["claims"][0]["evidence_criteria_ids"] = ["artifact"]
    duplicate = receipt()
    duplicate["criteria"] = [copy.deepcopy(duplicate["criteria"][0])]
    result = build(encoded(declared), [encoded(receipt()), encoded(duplicate)])
    assert result["claims"][0]["status"] == "unverifiable"


def test_wrong_task_and_duplicate_claim_ids_fail_closed() -> None:
    wrong = receipt()
    wrong["task_id"] = "other"
    try:
        build(encoded(source()), [encoded(wrong)])
    except ValueError as exc:
        assert "different task" in str(exc)
    else:
        raise AssertionError("wrong-task receipt accepted")
    declared = source()
    declared["claims"].append(copy.deepcopy(declared["claims"][0]))
    try:
        build(encoded(declared), [encoded(receipt())])
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("duplicate claim accepted")


def test_cli_preserves_outputs_then_strict_exits_for_review(tmp_path: Path) -> None:
    source_path = tmp_path / "claims.json"
    receipt_path = tmp_path / "receipt.json"
    output = tmp_path / "audit.json"
    card = tmp_path / "audit.md"
    source_path.write_bytes(encoded(source()))
    receipt_path.write_bytes(encoded(receipt()))
    result = CliRunner().invoke(cli, ["evidence", "claims", str(source_path), str(receipt_path), "--output", str(output), "--card", str(card), "--strict"])
    assert result.exit_code == 1, result.output
    artifact = json.loads(output.read_text(encoding="utf-8"))
    assert artifact["source_sha256"] == hashlib.sha256(source_path.read_bytes()).hexdigest()
    assert artifact["gate"] == "review_required"
    assert "Agent Claim Audit" in card.read_text(encoding="utf-8")
