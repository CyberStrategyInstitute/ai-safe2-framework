from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from safe2.adapters import evaluate_conformance
from safe2.cli import cli
from safe2.contracts import validate_artifact


def descriptor() -> dict:
    return {
        "schema_version": "safe2.adapter.v1",
        "adapter_id": "example.harness",
        "version": "1.0",
        "provider": {"name": "Example", "version": "2"},
        "evidence_types": ["harness"],
        "decision_scope": "evidence_only",
        "transport": "file",
        "privacy": {
            "content_collection": "metadata",
            "network_required": False,
            "credential_required": False,
        },
    }


def evidence() -> dict:
    return {
        "schema_version": "safe2.adapter-evidence.v1",
        "evidence_id": "e1",
        "adapter_id": "example.harness",
        "adapter_version": "1.0",
        "provider": {"name": "Example", "version": "2"},
        "evidence_type": "harness",
        "observed_at": "2026-10-03T00:00:00Z",
        "status": "complete",
        "decision_scope": "evidence_only",
        "conformance_claim": False,
        "coverage": {"inspected": ["task"], "gaps": []},
        "claims": [
            {
                "id": "c1",
                "name": "task_seen",
                "value": True,
                "basis": "observed",
                "source_ref": "event-1",
            }
        ],
        "payload": {"task": "t1"},
        "provenance": {"source": "export.json", "source_sha256": "0" * 64},
    }


def test_valid_adapter_specimen_passes() -> None:
    report = evaluate_conformance(descriptor(), [("valid.json", evidence())])
    assert report["status"] == "passed"
    assert report["summary"] == {"cases": 1, "passed": 1, "failed": 0}
    assert not validate_artifact("adapter-conformance-v1", report)


def test_false_conformance_claim_and_provider_drift_fail() -> None:
    specimen = evidence()
    specimen["conformance_claim"] = True
    specimen["provider"]["version"] = "different"
    report = evaluate_conformance(descriptor(), [("bad.json", specimen)])
    assert report["status"] == "failed"
    assert report["cases"][0]["structural_errors"]


def test_partial_requires_visible_gap() -> None:
    specimen = evidence()
    specimen["status"] = "partial"
    report = evaluate_conformance(descriptor(), [("partial.json", specimen)])
    assert report["status"] == "failed"
    assert report["cases"][0]["semantic_errors"][0]["rule"] == "COVERAGE-PARTIAL"


def test_cli_writes_report_and_refuses_overwrite(tmp_path: Path) -> None:
    descriptor_path = tmp_path / "adapter.json"
    specimen_path = tmp_path / "evidence.json"
    output = tmp_path / "report.json"
    descriptor_path.write_text(json.dumps(descriptor()), encoding="utf-8")
    specimen_path.write_text(json.dumps(evidence()), encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "adapter",
            "conformance",
            str(descriptor_path),
            str(specimen_path),
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.output
    first = output.read_bytes()
    again = runner.invoke(
        cli,
        [
            "adapter",
            "conformance",
            str(descriptor_path),
            str(specimen_path),
            "--output",
            str(output),
        ],
    )
    assert again.exit_code != 0
    assert output.read_bytes() == first


def test_duplicate_json_keys_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "duplicate.json"
    source.write_text(
        '{"schema_version":"safe2.adapter.v1","schema_version":"x"}', encoding="utf-8"
    )
    result = CliRunner().invoke(cli, ["adapter", "validate", str(source)])
    assert result.exit_code != 0
    assert "duplicate JSON object key" in result.output


def test_unavailable_evidence_cannot_retain_observed_claims() -> None:
    specimen = evidence()
    specimen["status"] = "unavailable"
    specimen["payload"] = None
    report = evaluate_conformance(descriptor(), [("unavailable.json", specimen)])
    assert report["status"] == "failed"
    assert any(row["rule"] == "UNAVAILABLE-CLAIMS" for row in report["cases"][0]["semantic_errors"])


def test_overflowing_json_number_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "overflow.json"
    source.write_text('{"schema_version":"safe2.adapter.v1","nested":{"value":1e400}}', encoding="utf-8")
    result = CliRunner().invoke(cli, ["adapter", "validate", str(source)])
    assert result.exit_code != 0
    assert "non-finite" in result.output
