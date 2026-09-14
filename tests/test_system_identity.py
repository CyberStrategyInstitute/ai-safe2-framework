"""System identity manifest trust-boundary and adversarial tests."""

from __future__ import annotations

import copy
import json
from importlib.resources import files
from pathlib import Path

import pytest
from click.testing import CliRunner

from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.evidence.manifest import create_manifest
from safe2.evidence.system_identity import ingest


def demo() -> dict:
    return json.loads(files("safe2.data").joinpath("system-identity-source-demo.json").read_text())


def payload(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode()


def component(value: dict, category: str) -> dict:
    return next(item for item in value["components"] if item["category"] == category)


def test_demo_binds_complete_composition_without_verifying_it():
    raw = payload(demo())
    result = ingest(raw)
    assert result["summary"]["components"] == 8
    assert result["summary"]["bindings"] == 7
    assert result["summary"]["coverage_complete"] == 8
    assert result["summary"]["unbound_components"] == 0
    assert result["source"]["sha256"]
    assert result["source"]["bytes"] == len(raw)
    assert result["source"]["authentication"] == "not_checked"
    assert result["identity_verified"] is False
    assert result["configuration_verified"] is False
    assert result["conformance_claim"] is False
    assert result["recommendations"] == []
    assert validate_artifact("system-identity-manifest-v1", result) == []


def test_system_fingerprint_is_order_and_provenance_independent():
    first = demo()
    second = copy.deepcopy(first)
    second["components"].reverse()
    second["bindings"].reverse()
    second["components"][0]["basis"] = "observed"
    second["components"][0]["source_ref"] = "different-source"
    second["bindings"][0]["binding_id"] = "different-record-id"
    assert ingest(payload(first))["system_fingerprint_sha256"] == ingest(payload(second))[
        "system_fingerprint_sha256"
    ]
    component(second, "harness")["version"] = "2.0.0"
    assert ingest(payload(first))["system_fingerprint_sha256"] != ingest(payload(second))[
        "system_fingerprint_sha256"
    ]


def test_not_applicable_is_distinct_from_missing():
    value = demo()
    skill_id = component(value, "skill")["component_id"]
    value["components"] = [item for item in value["components"] if item["component_id"] != skill_id]
    value["bindings"] = [item for item in value["bindings"] if skill_id not in (
        item["from_component_id"], item["to_component_id"]
    )]
    value["coverage"]["skill"] = {
        "status": "not_applicable", "basis": "declared", "source_ref": "config-1"
    }
    result = ingest(payload(value))
    assert result["summary"]["coverage_not_applicable"] == 1
    assert result["summary"]["coverage_missing"] == 0


@pytest.mark.parametrize("mutation", [
    "duplicate_component", "missing_model", "unknown_with_ref", "declared_without_ref",
    "mixed_unknown_authority", "duplicate_binding", "duplicate_relationship", "missing_endpoint", "self_binding",
    "missing_with_component", "not_applicable_with_component", "complete_without_component",
    "complete_unknown_component", "duplicate_evidence",
])
def test_ambiguous_or_contradictory_identity_is_rejected(mutation: str):
    value = demo()
    if mutation == "duplicate_component":
        value["components"][1]["component_id"] = value["components"][0]["component_id"]
    elif mutation == "missing_model":
        value["components"] = [item for item in value["components"] if item["category"] != "model"]
        value["bindings"] = [item for item in value["bindings"] if item["to_component_id"] != "model-1"]
        value["coverage"]["model"] = {"status": "missing", "basis": "unknown", "source_ref": None}
    elif mutation == "unknown_with_ref":
        value["components"][0].update(basis="unknown", source_ref="x")
    elif mutation == "declared_without_ref":
        value["bindings"][0]["source_ref"] = None
    elif mutation == "mixed_unknown_authority":
        component(value, "harness")["authority"] = ["unknown", "execute"]
    elif mutation == "duplicate_binding":
        value["bindings"][1]["binding_id"] = value["bindings"][0]["binding_id"]
    elif mutation == "duplicate_relationship":
        duplicate = copy.deepcopy(value["bindings"][0])
        duplicate["binding_id"] = "different-id"
        value["bindings"].append(duplicate)
    elif mutation == "missing_endpoint":
        value["bindings"][0]["to_component_id"] = "absent"
    elif mutation == "self_binding":
        value["bindings"][0]["to_component_id"] = value["bindings"][0]["from_component_id"]
    elif mutation == "missing_with_component":
        value["coverage"]["skill"] = {"status": "missing", "basis": "unknown", "source_ref": None}
    elif mutation == "not_applicable_with_component":
        value["coverage"]["skill"]["status"] = "not_applicable"
    elif mutation == "complete_without_component":
        value["components"] = [item for item in value["components"] if item["category"] != "skill"]
        value["bindings"] = [item for item in value["bindings"] if item["to_component_id"] != "skill-1"]
    elif mutation == "complete_unknown_component":
        component(value, "skill").update(basis="unknown", source_ref=None)
    else:
        value["evidence_refs"][1]["evidence_id"] = value["evidence_refs"][0]["evidence_id"]
    with pytest.raises(ValueError):
        ingest(payload(value))


@pytest.mark.parametrize("value", [{}, [], None, {"schema_version": "safe2.system-identity-source.v1"}])
def test_invalid_sources_rejected(value: object):
    with pytest.raises((TypeError, ValueError)):
        ingest(payload(value))


def test_duplicate_json_keys_and_oversize_rejected():
    with pytest.raises(ValueError):
        ingest(b'{"schema_version":"safe2.system-identity-source.v1","schema_version":"other"}')
    with pytest.raises(ValueError):
        ingest(b"x" * 1_000_001)


def test_strict_cli_passes_complete_demo_and_refuses_overwrite(tmp_path: Path):
    source = tmp_path / "source.json"
    output = tmp_path / "manifest.json"
    source.write_bytes(payload(demo()))
    result = CliRunner().invoke(cli, [
        "evidence", "system", str(source), "--output", str(output), "--strict",
    ])
    assert result.exit_code == 0
    assert json.loads(output.read_text())["configuration_verified"] is False
    second = CliRunner().invoke(cli, ["evidence", "system", str(source), "--output", str(output)])
    assert second.exit_code != 0


def test_strict_cli_writes_then_exits_one_for_gaps(tmp_path: Path):
    value = demo()
    component(value, "tool")["version"] = None
    value["coverage"]["tool"]["status"] = "partial"
    source = tmp_path / "source.json"
    output = tmp_path / "manifest.json"
    source.write_bytes(payload(value))
    result = CliRunner().invoke(cli, [
        "evidence", "system", str(source), "--output", str(output), "--strict",
    ])
    assert result.exit_code == 1
    written = json.loads(output.read_text())
    assert written["summary"]["coverage_partial"] == 1
    assert written["summary"]["unversioned_components"] == 1


@pytest.mark.parametrize("kind", ["source", "manifest"])
def test_evidence_manifest_recognizes_identity_contracts(tmp_path: Path, kind: str):
    raw = payload(demo())
    artifact = demo() if kind == "source" else ingest(raw)
    path = tmp_path / f"{kind}.json"
    path.write_text(json.dumps(artifact))
    result = create_manifest((path,), subject_id="demo-agent-system")
    assert result["summary"]["valid"] == 1
    assert result["artifacts"][0]["contract"] == f"system-identity-{kind}-v1"
    assert result["artifacts"][0]["integrity_verification"] == "not_applicable"


def test_input_not_mutated():
    value = demo()
    before = copy.deepcopy(value)
    ingest(payload(value))
    assert value == before
