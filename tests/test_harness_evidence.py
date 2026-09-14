"""Provider-neutral harness evidence intake and fail-closed coverage tests."""

from __future__ import annotations

import copy
import json
from importlib.resources import files
from pathlib import Path

import pytest
from click.testing import CliRunner

from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.evidence.harness import ingest
from safe2.evidence.manifest import create_manifest


def demo() -> dict:
    return json.loads(files("safe2.data").joinpath("harness-source-demo.json").read_text(encoding="utf-8"))


def payload(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode()


def test_demo_preserves_gaps_claim_and_source_binding():
    raw = payload(demo())
    result = ingest(raw)
    assert result["source"]["sha256"]
    assert result["source"]["bytes"] == len(raw)
    assert result["summary"] == {"coverage_complete": 2, "coverage_partial": 2,
        "coverage_missing": 3, "observed_events": 0, "declared_events": 3,
        "missing_events": 0, "total_events": 3}
    assert result["completion_claim"]["status"] == "claimed_complete"
    assert result["completion_verified"] is False
    assert result["billing_verified"] is False
    assert result["conformance_claim"] is False
    assert len(result["recommendations"]) == 6
    assert validate_artifact("harness-evidence-v1", result) == []


def test_native_observed_labels_still_do_not_verify_execution():
    value = demo()
    value["producer"]["kind"] = "native_export"
    for item in value["coverage"].values():
        item.update(status="complete", basis="observed", source_ref="native-log")
    for event in value["events"]:
        event.update(status="observed", source_ref="native-log")
    result = ingest(payload(value))
    assert result["summary"]["coverage_complete"] == 7
    assert result["summary"]["observed_events"] == 3
    assert result["recommendations"] == []
    assert result["source"]["authentication"] == "not_checked"
    assert result["completion_verified"] is False


@pytest.mark.parametrize("mutation", ["duplicate", "missing_ref", "false_missing", "unknown_usage", "claim_ref"])
def test_semantic_ambiguity_rejected(mutation):
    value = demo()
    if mutation == "duplicate":
        value["usage"][0]["event_id"] = value["events"][0]["event_id"]
    elif mutation == "missing_ref":
        value["events"][0]["source_ref"] = None
    elif mutation == "false_missing":
        value["coverage"]["tests"] = {"status": "missing", "basis": "declared", "source_ref": "x"}
    elif mutation == "unknown_usage":
        value["usage"][0].update(basis="unknown", value=1, source_ref=None)
    else:
        value["completion_claim"] = {"status": "not_claimed", "source_ref": "x"}
    with pytest.raises(ValueError):
        ingest(payload(value))


@pytest.mark.parametrize("value", [{}, [], None, {"schema_version": "safe2.harness-source.v1"}])
def test_invalid_sources_rejected(value):
    with pytest.raises((TypeError, ValueError)):
        ingest(payload(value))


def test_duplicate_json_keys_and_oversize_rejected():
    with pytest.raises(ValueError):
        ingest(b'{"schema_version":"safe2.harness-source.v1","schema_version":"other"}')
    with pytest.raises(ValueError):
        ingest(b"x" * 1_000_001)


def test_cli_writes_new_output_and_strict_reports_gaps(tmp_path: Path):
    source = tmp_path / "source.json"
    output = tmp_path / "result.json"
    source.write_bytes(payload(demo()))
    result = CliRunner().invoke(cli, ["evidence", "harness", str(source), "--output", str(output), "--strict"])
    assert result.exit_code == 1
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["summary"]["coverage_missing"] == 3
    assert written["completion_verified"] is False
    second = CliRunner().invoke(cli, ["evidence", "harness", str(source), "--output", str(output)])
    assert second.exit_code != 0


def test_manifest_recognizes_harness_evidence(tmp_path: Path):
    source = tmp_path / "source.json"
    source.write_text(json.dumps(ingest(payload(demo()))), encoding="utf-8")
    manifest = create_manifest((source,), subject_id="demo")
    assert manifest["summary"]["valid"] == 1
    assert manifest["artifacts"][0]["contract"] == "harness-evidence-v1"


def test_manifest_recognizes_attributed_source_without_authenticating_it(tmp_path: Path):
    source = tmp_path / "source.json"
    source.write_bytes(payload(demo()))
    manifest = create_manifest((source,), subject_id="demo")
    assert manifest["summary"]["valid"] == 1
    assert manifest["artifacts"][0]["contract"] == "harness-source-v1"
    assert manifest["artifacts"][0]["integrity_verification"] == "not_applicable"


def test_input_not_mutated():
    value = demo()
    before = copy.deepcopy(value)
    ingest(payload(value))
    assert value == before
