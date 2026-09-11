"""Adversarial replay of imported test claims, without running specimen code."""

import hashlib
import json

import pytest
from click.testing import CliRunner

from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.evidence.task_receipt import evaluate_task, render_receipt


def report():
    return {
        "schema_version": "safe2.test-result.v1", "task_id": "t1", "revision": "rev-1",
        "environment": "ci-linux", "source_ref": "ci-run-123", "exit_code": 0,
        "counts": {"total": 2, "passed": 2, "failed": 0, "errors": 0, "skipped": 0},
    }


def evaluate(tmp_path, result=None, raw=None, change=None):
    payload = raw if raw is not None else json.dumps(result or report()).encode()
    (tmp_path / "tests.json").write_bytes(payload)
    document = {
        "schema_version": "safe2.task-receipt-input.v1", "task_id": "t1",
        "parent_task_id": None, "harness": "test", "usage": [],
        "criteria": [{"id": "tests", "kind": "test_report", "path": "tests.json",
                      "expected_sha256": hashlib.sha256(payload).hexdigest(),
                      "expected_revision": "rev-1", "expected_environment": "ci-linux"}],
    }
    if change:
        document["criteria"][0].update(change)
    receipt = evaluate_task(document, tmp_path)
    assert validate_artifact("task-receipt-v1", receipt) == []
    assert receipt["completion_verified"] is False
    assert receipt["conformance_claim"] is False
    return receipt, document


def test_all_passed_is_report_consistency_only(tmp_path):
    receipt, _ = evaluate(tmp_path)
    assert receipt["criteria"][0]["status"] == "supported"
    assert "Imported report; execution not authenticated" in render_receipt(receipt)


@pytest.mark.parametrize("key", ["task_id", "revision", "environment"])
def test_stale_or_wrong_binding_unverifiable(tmp_path, key):
    result = report()
    result[key] = "other"
    receipt, _ = evaluate(tmp_path, result)
    assert receipt["criteria"][0]["reason"] == "test_report_binding_mismatch"
    assert receipt["criteria"][0]["status"] == "unverifiable"


@pytest.mark.parametrize("key", ["failed", "errors"])
def test_failure_cannot_be_success_even_with_exit_zero(tmp_path, key):
    result = report()
    result["counts"]["passed"] = 1
    result["counts"][key] = 1
    receipt, _ = evaluate(tmp_path, result)
    assert receipt["criteria"][0]["status"] == "contradicted"


def test_nonzero_exit_contradicts_all_passed(tmp_path):
    result = report()
    result["exit_code"] = 1
    receipt, _ = evaluate(tmp_path, result)
    assert receipt["criteria"][0]["status"] == "contradicted"


@pytest.mark.parametrize("counts,reason", [
    ({"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}, "test_report_no_tests"),
    ({"total": 2, "passed": 1, "failed": 0, "errors": 0, "skipped": 1}, "test_report_has_skips"),
    ({"total": 2, "passed": 0, "failed": 0, "errors": 0, "skipped": 2}, "test_report_has_skips"),
    ({"total": 2, "passed": 3, "failed": 0, "errors": 0, "skipped": 0}, "test_report_inconsistent_counts"),
])
def test_incomplete_and_inconsistent_reports(tmp_path, counts, reason):
    result = report()
    result["counts"] = counts
    receipt, _ = evaluate(tmp_path, result)
    assert receipt["criteria"][0]["status"] == "unverifiable"
    assert receipt["criteria"][0]["reason"] == reason


@pytest.mark.parametrize("raw", [b'{}', b'not JSON', b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}'])
def test_malformed_reports(tmp_path, raw):
    receipt, _ = evaluate(tmp_path, raw=raw)
    assert receipt["criteria"][0]["reason"] == "test_report_invalid"


def test_changed_report_is_inapplicable_not_failed_tests(tmp_path):
    receipt, _ = evaluate(tmp_path, change={"expected_sha256": "0" * 64})
    assert receipt["criteria"][0]["status"] == "unverifiable"
    assert receipt["criteria"][0]["reason"] == "test_report_digest_mismatch"


def test_cli_with_failing_report(tmp_path):
    result = report()
    result["exit_code"] = 1
    _, document = evaluate(tmp_path, result)
    source = tmp_path / "input.json"
    source.write_text(json.dumps(document), encoding="utf-8")
    run = CliRunner().invoke(cli, ["feedback", "receipt", str(source), "--artifact-root", str(tmp_path)])
    assert run.exit_code == 0  # Reporting success, NOT a passing gate.
    assert json.loads(run.output)["counts"]["contradicted"] == 1


def test_missing_expected_context_rejected(tmp_path):
    _, document = evaluate(tmp_path)
    del document["criteria"][0]["expected_revision"]
    with pytest.raises(ValueError):
        evaluate_task(document, tmp_path)
