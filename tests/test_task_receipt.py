"""Receipts must never promote a reference or byte match into completed work."""

import hashlib
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.evidence.task_receipt import evaluate_task, render_receipt


def specimen(tmp_path: Path) -> dict:
    (tmp_path / "artifact.txt").write_bytes(b"hello\n")
    return {
        "schema_version": "safe2.task-receipt-input.v1", "task_id": "task-1",
        "parent_task_id": None, "harness": "test-harness",
        "criteria": [{"id": "artifact", "kind": "artifact_sha256", "path": "artifact.txt",
                      "expected_sha256": hashlib.sha256(b"hello\n").hexdigest()}],
        "usage": [],
    }


def test_matching_bytes_are_not_completion(tmp_path):
    result = evaluate_task(specimen(tmp_path), tmp_path)
    assert result["counts"] == {"supported": 1, "contradicted": 0, "unverifiable": 0}
    assert result["completion_verified"] is False
    assert result["conformance_claim"] is False
    assert validate_artifact("task-receipt-v1", result) == []
    assert "not assumed to be zero" in render_receipt(result)
    assert "Task completion is not verified" in render_receipt(result)


def test_output_contract_rejects_completion_promotion(tmp_path):
    result = evaluate_task(specimen(tmp_path), tmp_path)
    result["completion_verified"] = True
    assert validate_artifact("task-receipt-v1", result)


def test_mismatch_and_missing_are_distinct(tmp_path):
    document = specimen(tmp_path)
    (tmp_path / "artifact.txt").write_bytes(b"different")
    assert evaluate_task(document, tmp_path)["criteria"][0]["status"] == "contradicted"
    (tmp_path / "artifact.txt").unlink()
    assert evaluate_task(document, tmp_path)["criteria"][0]["status"] == "unverifiable"


@pytest.mark.parametrize("path", ["../secret", "/etc/passwd", "C:/secret", "x\\y", "x//y", "./x", "x:ads", "x\n"])
def test_paths_cannot_escape_root(tmp_path, path):
    document = specimen(tmp_path)
    document["criteria"][0]["path"] = path
    with pytest.raises(ValueError):
        evaluate_task(document, tmp_path)


def test_size_limit_is_unverifiable(tmp_path):
    document = specimen(tmp_path)
    (tmp_path / "artifact.txt").write_bytes(b"x" * 1_000_001)
    assert evaluate_task(document, tmp_path)["counts"]["unverifiable"] == 1


@pytest.mark.parametrize("field", ["criteria", "usage"])
def test_duplicate_ids_rejected(tmp_path, field):
    document = specimen(tmp_path)
    if field == "usage":
        document[field] = [{"event_id": "u1", "metric": "input_tokens", "value": None,
                            "basis": "unknown", "source_ref": None}]
    document[field].append(document[field][0].copy())
    with pytest.raises(ValueError, match="unique"):
        evaluate_task(document, tmp_path)


@pytest.mark.parametrize("value,basis,source", [(0, "unknown", None), (None, "estimated", "s"), (4, "provider_reported", None), (1.5, "provider_reported", "s")])
def test_usage_cannot_invent_precision(tmp_path, value, basis, source):
    document = specimen(tmp_path)
    document["usage"] = [{"event_id": "u1", "metric": "input_tokens", "value": value,
                          "basis": basis, "source_ref": source}]
    with pytest.raises(ValueError):
        evaluate_task(document, tmp_path)


def test_usage_stays_declared_not_verified(tmp_path):
    document = specimen(tmp_path)
    document["usage"] = [{"event_id": "u1", "metric": "api_cost_usd", "value": 0.3,
                          "basis": "estimated", "source_ref": "price-table-2026-09-10"}]
    result = evaluate_task(document, tmp_path)
    assert result["usage_verification"] == "unverified_source_declarations"
    assert result["usage"] == document["usage"]


def test_unsupported_verifier_and_self_parent_rejected(tmp_path):
    document = specimen(tmp_path)
    document["parent_task_id"] = "task-1"
    with pytest.raises(ValueError):
        evaluate_task(document, tmp_path)
    document["parent_task_id"] = None
    document["criteria"][0]["kind"] = "execute-shell"
    with pytest.raises(ValueError):
        evaluate_task(document, tmp_path)


def test_cli_no_overwrite_and_reporting_exit(tmp_path):
    document = specimen(tmp_path)
    document["criteria"][0]["expected_sha256"] = "0" * 64
    source = tmp_path / "input.json"
    source.write_text(json.dumps(document), encoding="utf-8")
    arguments = ["feedback", "receipt", str(source), "--artifact-root", str(tmp_path)]
    result = CliRunner().invoke(cli, arguments)
    assert result.exit_code == 0
    assert json.loads(result.output)["counts"]["contradicted"] == 1
    output = tmp_path / "result.md"
    result = CliRunner().invoke(cli, arguments + ["--format", "markdown", "--output", str(output)])
    assert result.exit_code == 0
    original = output.read_bytes()
    assert CliRunner().invoke(cli, arguments + ["--output", str(output)]).exit_code != 0
    assert output.read_bytes() == original


@pytest.mark.parametrize("body", ['{"task_id":"a","task_id":"b"}', '{"value":NaN}', '{"value":1e999}'])
def test_ambiguous_json_rejected(tmp_path, body):
    source = tmp_path / "input.json"
    source.write_text(body, encoding="utf-8")
    result = CliRunner().invoke(cli, ["feedback", "receipt", str(source), "--artifact-root", str(tmp_path)])
    assert result.exit_code != 0


def test_symlink_unverifiable(tmp_path):
    document = specimen(tmp_path)
    link = tmp_path / "alias.txt"
    try:
        link.symlink_to(tmp_path / "artifact.txt")
    except (OSError, NotImplementedError):
        pytest.skip("Platform lacks symlink permission")
    document["criteria"][0]["path"] = "alias.txt"
    assert evaluate_task(document, tmp_path)["counts"]["unverifiable"] == 1
