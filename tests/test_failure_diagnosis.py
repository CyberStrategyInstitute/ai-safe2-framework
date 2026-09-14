"""Evidence-bounded failure localization and trust-boundary tests."""

from __future__ import annotations

import copy
import json
from importlib.resources import files
from pathlib import Path

import pytest
from click.testing import CliRunner

from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.evidence.diagnosis import diagnose
from safe2.evidence.diagnosis_card import render
from safe2.evidence.manifest import create_manifest
from safe2.evidence.system_identity import ingest as ingest_identity


def source() -> dict:
    return json.loads(files("safe2.data").joinpath("failure-source-demo.json").read_text())


def identity() -> dict:
    raw = files("safe2.data").joinpath("system-identity-source-demo.json").read_bytes()
    return ingest_identity(raw)


def payload(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode()


def run(value: dict | None = None, identity_value: dict | None = None) -> dict:
    return diagnose(payload(value or source()), payload(identity_value or identity()))


def test_demo_ranks_boundary_and_preserves_non_claims():
    result = run()
    assert result["diagnosis_status"] == "ranked_candidate"
    assert result["primary_candidate_id"] == "candidate-harness-tool"
    assert result["candidates"][0]["location"]["primary_category"] == "harness"
    assert result["candidates"][0]["location"]["interacting_category"] == "tool"
    assert result["candidates"][0]["evidence_assessment"]["level"] == "strong"
    assert result["candidates"][1]["evidence_assessment"]["level"] == "contradicted"
    assert result["root_cause_verified"] is False
    assert result["probability_estimate"] is False
    assert result["conformance_claim"] is False
    assert validate_artifact("failure-diagnosis-v1", result) == []


def test_source_and_identity_bytes_are_bound_separately():
    result = run()
    assert result["source"]["sha256"]
    assert result["system_identity"]["manifest_sha256"]
    assert result["source"]["sha256"] != result["system_identity"]["manifest_sha256"]
    assert result["system_identity"]["configuration_verified"] is False


def test_tied_candidates_do_not_create_primary_diagnosis():
    value = source()
    duplicate = copy.deepcopy(value["candidates"][0])
    duplicate["candidate_id"] = "candidate-harness-tool-alternative"
    duplicate["failure_mode"] = "orchestration_error"
    value["candidates"].append(duplicate)
    result = run(value)
    assert result["diagnosis_status"] == "competing_candidates"
    assert result["primary_candidate_id"] is None


def test_missing_only_support_is_insufficient():
    value = source()
    value["observations"] = [{
        "observation_id": "obs-missing", "kind": "artifact_state", "basis": "missing",
        "directness": "unknown", "source_id": None, "source_ref": None,
        "component_ids": ["harness-1"], "statement": "Artifact state was not collected.",
    }]
    value["candidates"] = [{
        "candidate_id": "candidate-unknown", "primary_component_id": "harness-1",
        "interacting_component_id": None, "failure_mode": "unknown",
        "description": "The available record cannot localize the failure.",
        "supporting_observation_ids": ["obs-missing"], "contradicting_observation_ids": [],
        "assumptions": [], "repair_owner": "unknown",
        "recommended_action": "Collect artifact and execution evidence.",
    }]
    result = run(value)
    assert result["diagnosis_status"] == "insufficient_evidence"
    assert result["primary_candidate_id"] is None
    assert result["evidence_summary"]["missing"] == 1


def test_declared_support_is_limited_not_probability():
    value = source()
    for observation in value["observations"]:
        observation.update(basis="declared", directness="indirect")
    for candidate in value["candidates"]:
        candidate["contradicting_observation_ids"] = []
    result = run(value)
    assert result["candidates"][0]["evidence_assessment"]["level"] == "limited"
    assert result["probability_estimate"] is False


@pytest.mark.parametrize("mutation", [
    "subject", "fingerprint", "duplicate_observation", "unknown_observation_component",
    "missing_attributed", "missing_direct", "observed_unattributed", "duplicate_candidate",
    "unknown_candidate_component", "self_interaction", "evidence_overlap", "unknown_evidence",
])
def test_ambiguous_or_unbound_diagnosis_is_rejected(mutation: str):
    value = source()
    if mutation == "subject":
        value["subject"]["subject_id"] = "other"
    elif mutation == "fingerprint":
        value["subject"]["system_fingerprint_sha256"] = "f" * 64
    elif mutation == "duplicate_observation":
        value["observations"][1]["observation_id"] = value["observations"][0]["observation_id"]
    elif mutation == "unknown_observation_component":
        value["observations"][0]["component_ids"] = ["absent"]
    elif mutation == "missing_attributed":
        value["observations"][0]["basis"] = "missing"
        value["observations"][0]["directness"] = "unknown"
    elif mutation == "missing_direct":
        value["observations"][0].update(basis="missing", source_id=None, source_ref=None)
    elif mutation == "observed_unattributed":
        value["observations"][0]["source_ref"] = None
    elif mutation == "duplicate_candidate":
        value["candidates"][1]["candidate_id"] = value["candidates"][0]["candidate_id"]
    elif mutation == "unknown_candidate_component":
        value["candidates"][0]["primary_component_id"] = "absent"
    elif mutation == "self_interaction":
        value["candidates"][0]["interacting_component_id"] = "harness-1"
    elif mutation == "evidence_overlap":
        value["candidates"][0]["contradicting_observation_ids"] = ["obs-tool-success"]
    else:
        value["candidates"][0]["supporting_observation_ids"] = ["absent"]
    with pytest.raises(ValueError):
        run(value)


@pytest.mark.parametrize("value", [{}, [], None, {"schema_version": "safe2.failure-source.v1"}])
def test_invalid_failure_sources_rejected(value: object):
    with pytest.raises((TypeError, ValueError)):
        diagnose(payload(value), payload(identity()))


def test_duplicate_keys_and_size_limits_rejected():
    with pytest.raises(ValueError):
        diagnose(b'{"schema_version":"safe2.failure-source.v1","schema_version":"x"}', payload(identity()))
    with pytest.raises(ValueError):
        diagnose(b"x" * 1_000_001, payload(identity()))


def test_card_separates_evidence_assumptions_and_claim_limits():
    value = source()
    value["candidates"][0]["description"] = "Unsafe <script>alert(1)</script>\nnext"
    card = render(run(value))
    assert "&lt;script&gt;" in card
    assert "\nnext" not in card
    assert "**Assumptions:** None" in card
    assert "Root cause verified:** `false`" in card
    assert "Probability estimate:** `false`" in card


def test_cli_writes_json_and_card_then_refuses_overwrite(tmp_path: Path):
    source_path = tmp_path / "failure.json"
    identity_path = tmp_path / "identity.json"
    output = tmp_path / "diagnosis.json"
    card = tmp_path / "diagnosis.md"
    source_path.write_bytes(payload(source()))
    identity_path.write_bytes(payload(identity()))
    result = CliRunner().invoke(cli, [
        "evidence", "diagnose", str(source_path), "--system-identity", str(identity_path),
        "--output", str(output), "--card", str(card), "--strict",
    ])
    assert result.exit_code == 0
    assert json.loads(output.read_text())["primary_candidate_id"] == "candidate-harness-tool"
    assert "Failure Localization Card" in card.read_text()
    second = CliRunner().invoke(cli, [
        "evidence", "diagnose", str(source_path), "--system-identity", str(identity_path),
        "--output", str(output),
    ])
    assert second.exit_code != 0


def test_cli_rejects_same_json_and_card_destination_before_writing(tmp_path: Path):
    source_path = tmp_path / "failure.json"
    identity_path = tmp_path / "identity.json"
    output = tmp_path / "collision.json"
    source_path.write_bytes(payload(source()))
    identity_path.write_bytes(payload(identity()))
    result = CliRunner().invoke(cli, [
        "evidence", "diagnose", str(source_path), "--system-identity", str(identity_path),
        "--output", str(output), "--card", str(output),
    ])
    assert result.exit_code != 0
    assert not output.exists()


def test_strict_cli_exits_one_after_writing_limited_result(tmp_path: Path):
    value = source()
    for observation in value["observations"]:
        observation.update(basis="declared", directness="indirect")
    for candidate in value["candidates"]:
        candidate["contradicting_observation_ids"] = []
    source_path = tmp_path / "failure.json"
    identity_path = tmp_path / "identity.json"
    output = tmp_path / "diagnosis.json"
    source_path.write_bytes(payload(value))
    identity_path.write_bytes(payload(identity()))
    result = CliRunner().invoke(cli, [
        "evidence", "diagnose", str(source_path), "--system-identity", str(identity_path),
        "--output", str(output), "--strict",
    ])
    assert result.exit_code == 1
    assert output.exists()


@pytest.mark.parametrize("kind", ["source", "diagnosis"])
def test_evidence_manifest_recognizes_failure_contracts(tmp_path: Path, kind: str):
    artifact = source() if kind == "source" else run()
    path = tmp_path / f"{kind}.json"
    path.write_text(json.dumps(artifact))
    result = create_manifest((path,), subject_id="demo-agent-system")
    assert result["summary"]["valid"] == 1
    assert result["artifacts"][0]["contract"] == f"failure-{kind}-v1"


def test_inputs_not_mutated():
    failure, system = source(), identity()
    before_failure, before_system = copy.deepcopy(failure), copy.deepcopy(system)
    diagnose(payload(failure), payload(system))
    assert failure == before_failure
    assert system == before_system
