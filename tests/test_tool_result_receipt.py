"""Disclosure and success are separate: replay the full tool-outcome matrix."""

import hashlib
import json

import pytest
from click.testing import CliRunner

from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.evidence.task_receipt import evaluate_task, render_receipt


def specimen(tmp_path, outcome="unavailable", claim="succeeded", **changes):
    report = {
        "schema_version": "safe2.tool-result.v1", "task_id": "task-1",
        "revision": "rev-1", "environment": "sandbox", "source_ref": "event-1",
        "call_id": "call-1", "tool": "search", "outcome": outcome,
    }
    report.update(changes)
    payload = json.dumps(report).encode()
    (tmp_path / "tool.json").write_bytes(payload)
    return {
        "schema_version": "safe2.task-receipt-input.v1", "task_id": "task-1",
        "parent_task_id": None, "harness": "replay", "usage": [],
        "criteria": [{
            "id": "search-claim", "kind": "tool_report", "path": "tool.json",
            "expected_sha256": hashlib.sha256(payload).hexdigest(),
            "expected_revision": "rev-1", "expected_environment": "sandbox",
            "expected_call_id": "call-1", "expected_tool": "search", "claimed_outcome": claim,
        }],
    }


@pytest.mark.parametrize("outcome", ["succeeded", "failed", "unavailable", "not_attempted", "unknown"])
@pytest.mark.parametrize("claim", ["succeeded", "failed", "unavailable"])
def test_claim_outcome_matrix(tmp_path, outcome, claim):
    receipt = evaluate_task(specimen(tmp_path, outcome, claim), tmp_path)
    expected = "unverifiable" if outcome == "unknown" else (
        "supported" if outcome == claim else "contradicted"
    )
    assert receipt["criteria"][0]["status"] == expected
    assert receipt["completion_verified"] is False
    assert receipt["conformance_claim"] is False
    assert validate_artifact("task-receipt-v1", receipt) == []


@pytest.mark.parametrize("key", ["task_id", "revision", "environment", "call_id", "tool"])
def test_unrelated_evidence_is_not_false_claim(tmp_path, key):
    receipt = evaluate_task(specimen(tmp_path, **{key: "different"}), tmp_path)
    assert receipt["criteria"][0]["reason"] == "tool_report_binding_mismatch"
    assert receipt["counts"]["unverifiable"] == 1


@pytest.mark.parametrize("raw", [b'{}', b'not json', b'{"x":1,"x":2}', b'{"x":NaN}'])
def test_invalid_evidence_is_unverifiable(tmp_path, raw):
    document = specimen(tmp_path)
    (tmp_path / "tool.json").write_bytes(raw)
    document["criteria"][0]["expected_sha256"] = hashlib.sha256(raw).hexdigest()
    receipt = evaluate_task(document, tmp_path)
    assert receipt["criteria"][0]["reason"] == "tool_report_invalid"


def test_changed_evidence_is_not_claim_contradiction(tmp_path):
    document = specimen(tmp_path)
    (tmp_path / "tool.json").write_bytes(b'{}')
    receipt = evaluate_task(document, tmp_path)
    assert receipt["criteria"][0]["reason"] == "tool_report_digest_mismatch"
    assert receipt["counts"]["unverifiable"] == 1


def test_honest_blocker_is_not_task_completion(tmp_path):
    receipt = evaluate_task(specimen(tmp_path, claim="unavailable"), tmp_path)
    body = render_receipt(receipt)
    assert "claimed unavailable; reported unavailable" in body
    assert "Task completion is not verified" in body
    assert receipt["counts"]["supported"] == 1
    assert receipt["completion_verified"] is False


@pytest.mark.parametrize("key", ["expected_tool", "expected_call_id", "claimed_outcome"])
def test_tool_context_required(tmp_path, key):
    document = specimen(tmp_path)
    del document["criteria"][0][key]
    with pytest.raises(ValueError):
        evaluate_task(document, tmp_path)


def test_cli_reports_conflict_not_exit_gate(tmp_path):
    document = specimen(tmp_path)
    source = tmp_path / "input.json"
    source.write_text(json.dumps(document), encoding="utf-8")
    run = CliRunner().invoke(cli, ["feedback", "receipt", str(source), "--artifact-root", str(tmp_path)])
    assert run.exit_code == 0
    assert json.loads(run.output)["counts"]["contradicted"] == 1
