"""Operational truth must correlate evidence without promoting it into proof."""

from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from pathlib import Path

import pytest
from click.testing import CliRunner

from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.evidence.harness import ingest
from safe2.evidence.manifest import create_manifest
from safe2.evidence.operational_truth import build
from safe2.evidence.task_receipt import evaluate_task


def encoded(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode()


def policy(*receipts: dict) -> dict:
    return {
        "schema_version": "safe2.operational-truth-source.v1",
        "task_id": "task-1", "revision": "rev-1",
        "revision_receipt_sha256": [hashlib.sha256(encoded(item)).hexdigest() for item in receipts],
        "required_domains": ["task_lifecycle", "tool_calls", "artifacts", "tests",
                             "usage", "environment_state", "completion_claim"],
        "decision_owner": "release-owner", "assumptions": [], "exclusions": [],
    }


def harness(*, complete: bool = True, task_id: str = "task-1", revision: str = "rev-1",
            claim: str = "claimed_complete", export_id: str = "demo-export-1") -> dict:
    source = json.loads(files("safe2.data").joinpath("harness-source-demo.json").read_text())
    source["task"].update(task_id=task_id, revision=revision)
    source["producer"]["export_id"] = export_id
    source["completion_claim"]["status"] = claim
    if complete:
        source["producer"]["kind"] = "native_export"
        for item in source["coverage"].values():
            item.update(status="complete", basis="observed", source_ref="native-record")
        for item in source["events"]:
            item.update(status="observed", source_ref="native-record")
    return ingest(encoded(source))


def receipt(tmp_path: Path, *, task_id: str = "task-1", contradicted: bool = False) -> dict:
    body = b"actual\n"
    (tmp_path / "artifact.txt").write_bytes(body)
    expected = hashlib.sha256(b"different\n" if contradicted else body).hexdigest()
    source = {
        "schema_version": "safe2.task-receipt-input.v1", "task_id": task_id,
        "parent_task_id": None, "harness": "generic-agent",
        "criteria": [{"id": "artifact", "kind": "artifact_sha256", "path": "artifact.txt",
                      "expected_sha256": expected}], "usage": [],
    }
    return evaluate_task(source, tmp_path)


def test_supported_evidence_is_decision_ready_not_verified(tmp_path: Path):
    task_receipt = receipt(tmp_path)
    result = build(encoded(policy(task_receipt)), [encoded(harness()), encoded(task_receipt)])
    assert result["gate"] == "ready_for_human_decision"
    assert result["completion"]["assessment"] == "supported_by_supplied_evidence"
    assert result["completion_verified"] is False
    assert result["billing_verified"] is False
    assert result["conformance_claim"] is False
    assert validate_artifact("operational-truth-manifest-v1", result) == []


def test_claim_without_receipt_and_incomplete_coverage_requires_review():
    result = build(encoded(policy()), [encoded(harness(complete=False))])
    assert result["gate"] == "review"
    assert result["completion"]["assessment"] == "insufficient_evidence"
    assert "completion_claim_lacks_supported_receipt" in result["gaps"]


def test_contradiction_and_identity_mismatch_hold(tmp_path: Path):
    bad_receipt = receipt(tmp_path, contradicted=True)
    contradicted = build(encoded(policy(bad_receipt)), [encoded(harness()), encoded(bad_receipt)])
    assert contradicted["gate"] == "hold"
    assert contradicted["completion"]["assessment"] == "contradicted"
    mismatched = build(encoded(policy()), [encoded(harness(task_id="other"))])
    assert mismatched["gate"] == "hold"
    assert "task_id_mismatch" in mismatched["conflicts"]


def test_conflicting_usage_ownership_holds_while_identical_copy_deduplicates(tmp_path: Path):
    task_receipt = receipt(tmp_path)
    task_receipt["usage"] = [{"event_id": "usage-elapsed", "metric": "elapsed_ms", "value": 99,
                              "basis": "estimated", "source_ref": "different-source"}]
    conflict = build(encoded(policy(task_receipt)), [encoded(harness()), encoded(task_receipt)])
    assert conflict["gate"] == "hold"
    assert conflict["usage"]["duplicate_ownership"] == 1
    task_receipt["usage"][0].update(value=1200, source_ref="operator-note-1")
    deduplicated = build(encoded(policy(task_receipt)), [encoded(harness()), encoded(task_receipt)])
    assert deduplicated["usage"] == {"events": 1, "duplicate_ownership": 0, "billing_verified": False}


def test_receipt_without_revision_binding_cannot_support_completion(tmp_path: Path):
    task_receipt = receipt(tmp_path)
    result = build(encoded(policy()), [encoded(harness()), encoded(task_receipt)])
    assert result["gate"] == "review"
    assert result["completion"]["assessment"] == "insufficient_evidence"
    assert "completion_receipt_not_bound_to_revision" in result["gaps"]


def test_conflicting_completion_claims_hold_even_with_supported_receipt(tmp_path: Path):
    task_receipt = receipt(tmp_path)
    result = build(encoded(policy(task_receipt)), [encoded(harness()),
                   encoded(harness(claim="claimed_incomplete", export_id="second-export")),
                   encoded(task_receipt)])
    assert result["gate"] == "hold"
    assert result["completion"]["assessment"] == "contradicted"
    assert "completion_claim_conflict" in result["conflicts"]


def test_one_incomplete_harness_cannot_be_hidden_by_complete_harness():
    complete = harness()
    incomplete = harness(complete=False, export_id="second-export")
    result = build(encoded(policy()), [encoded(complete), encoded(incomplete)])
    assert result["gate"] == "review"
    assert result["coverage"]["artifacts"] == "missing"


def test_duplicate_artifact_and_unsupported_contract_rejected():
    artifact = encoded(harness())
    with pytest.raises(ValueError, match="Duplicate"):
        build(encoded(policy()), [artifact, artifact])
    with pytest.raises(ValueError, match="Unsupported"):
        build(encoded(policy()), [encoded({"schema_version": "unknown"})])


def test_cli_writes_truth_and_card_and_strict_is_honest(tmp_path: Path):
    policy_path, evidence_path = tmp_path / "policy.json", tmp_path / "evidence.json"
    output, card = tmp_path / "truth.json", tmp_path / "truth.md"
    policy_path.write_bytes(encoded(policy()))
    evidence_path.write_bytes(encoded(harness(complete=False)))
    result = CliRunner().invoke(cli, ["evidence", "truth", str(policy_path), str(evidence_path),
                                      "--output", str(output), "--card", str(card), "--strict"])
    assert result.exit_code == 1
    assert json.loads(output.read_text())["gate"] == "review"
    assert "Completion verified: `false`" in card.read_text()
    second = CliRunner().invoke(cli, ["evidence", "truth", str(policy_path), str(evidence_path),
                                      "--output", str(output), "--card", str(card)])
    assert second.exit_code != 0


def test_cli_rolls_back_json_when_card_write_fails(tmp_path: Path, monkeypatch):
    import safe2.challenge.io as artifact_io

    policy_path, evidence_path = tmp_path / "policy.json", tmp_path / "evidence.json"
    output, card = tmp_path / "truth.json", tmp_path / "truth.md"
    policy_path.write_bytes(encoded(policy()))
    evidence_path.write_bytes(encoded(harness(complete=False)))
    original = artifact_io.write_text
    calls = 0

    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            Path(args[0]).write_text("partial", encoding="utf-8")
            raise OSError("simulated card failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(artifact_io, "write_text", fail_second)
    result = CliRunner().invoke(cli, ["evidence", "truth", str(policy_path), str(evidence_path),
                                      "--output", str(output), "--card", str(card)])
    assert result.exit_code != 0
    assert not output.exists()
    assert not card.exists()


def test_manifest_recognizes_policy_and_result(tmp_path: Path):
    policy_path, result_path = tmp_path / "policy.json", tmp_path / "result.json"
    policy_path.write_bytes(encoded(policy()))
    result_path.write_bytes(encoded(build(encoded(policy()), [encoded(harness(complete=False))])))
    manifest = create_manifest((policy_path, result_path), subject_id="truth")
    assert manifest["summary"]["valid"] == 2
    assert {item["contract"] for item in manifest["artifacts"]} == {
        "operational-truth-source-v1", "operational-truth-manifest-v1"
    }
