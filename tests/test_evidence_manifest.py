from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

from click.testing import CliRunner
from jsonschema import Draft202012Validator

from safe2.cli import cli
from safe2.discovery.integrity import seal_inventory
from safe2.evidence.friction import record_event
from safe2.evidence.manifest import create_manifest, verify_manifest
from safe2.evidence.nexus import collect as collect_nexus

REPO_ROOT = Path(__file__).resolve().parent.parent


def _write(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _discovery(root: Path) -> dict[str, object]:
    return seal_inventory(
        {
            "schema_version": "safe2.discovery.v1",
            "collected_at": "2026-09-04T00:00:00+00:00",
            "scope": {"type": "local", "root": str(root)},
            "privacy": {
                "mode": "metadata_only",
                "secret_values_collected": False,
                "configuration_contents_collected": False,
            },
            "harnesses": [],
            "environments": [{"id": "host", "type": "operating_system"}],
            "shells": [],
            "targets": [],
            "summary": {
                "harnesses_detected": 0,
                "execution_environments": 1,
                "shells_detected": 0,
                "assessment_status": "inventory_only",
            },
            "limitations": [],
        }
    )


def test_manifest_binds_valid_heterogeneous_evidence(tmp_path: Path):
    discovery = _write(tmp_path / "discovery.json", _discovery(tmp_path))
    friction = _write(
        tmp_path / "friction.json",
        record_event(
            category="missing_evidence",
            outcome="blocked",
            severity="high",
            summary="Evidence was unavailable.",
        ),
    )
    result = create_manifest((discovery, friction), subject_id="workstation-1")
    assert result["summary"] == {"artifacts": 2, "valid": 2, "invalid": 0}
    assert all(row["integrity_verification"] == "valid" for row in result["artifacts"])
    assert len(result["integrity_sha256"]) == 64
    assert verify_manifest(result) == "valid"

    schema = json.loads(
        files("safe2.data").joinpath("run-manifest-v1.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(result)


def test_manifest_retains_unknown_and_tampered_evidence_as_invalid(tmp_path: Path):
    unknown = _write(
        tmp_path / "unknown.json", {"schema_version": "vendor.future.v9 SECRET_VALUE"}
    )
    tampered_event = record_event(
        category="context_loss",
        outcome="blocked",
        severity="medium",
        summary="Original.",
    )
    tampered_event["summary"] = "Changed."
    tampered = _write(tmp_path / "tampered.json", tampered_event)
    result = create_manifest((unknown, tampered), subject_id="workstation-1")
    assert result["summary"]["invalid"] == 2
    assert result["artifacts"][0]["error"] == "unknown_schema_version"
    assert result["artifacts"][0]["schema_version"] is None
    assert "SECRET_VALUE" not in json.dumps(result)
    assert result["artifacts"][1]["integrity_verification"] == "invalid"


def test_manifest_can_bind_policy_decisions_and_prior_manifests(tmp_path: Path):
    decision = _write(
        tmp_path / "decision.json",
        {
            "schema_version": "safe2.environment-policy-decision.v1",
            "policy_id": "test",
            "disposition": "ALLOW",
            "exit_code": 0,
            "violations": [],
            "unmet_prerequisites": [],
            "facts": {
                "posture_disposition": "REVIEW",
                "finding_counts": {},
                "drift_changes": 0,
                "baseline_integrity": "valid",
            },
            "interpretation": "Scoped local policy result.",
        },
    )
    prior_value = create_manifest((decision,), subject_id="host")
    prior = _write(tmp_path / "prior-manifest.json", prior_value)
    result = create_manifest((decision, prior), subject_id="host")
    assert result["summary"]["invalid"] == 0
    assert result["artifacts"][0]["contract"] == "environment-policy-decision-v1"
    assert result["artifacts"][1]["integrity_verification"] == "valid"


def test_manifest_binds_native_nexus_evidence(tmp_path: Path):
    nexus = _write(tmp_path / "nexus.json", collect_nexus(REPO_ROOT / "NEXUS"))
    result = create_manifest((nexus,), subject_id="nexus-local")
    assert result["summary"] == {"artifacts": 1, "valid": 1, "invalid": 0}
    assert result["artifacts"][0]["contract"] == "nexus-evidence-v1"


def test_manifest_cli_strict_exit_is_agent_safe(tmp_path: Path):
    artifact = _write(tmp_path / "unknown.json", {"schema_version": "unknown"})
    output = tmp_path / "manifest.json"
    result = CliRunner().invoke(
        cli,
        [
            "evidence",
            "manifest",
            str(artifact),
            "--subject-id",
            "agent-host",
            "--output",
            str(output),
            "--strict",
        ],
    )
    assert result.exit_code == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["summary"]["invalid"] == 1
    assert "vendor" not in json.dumps(payload)


def test_evidence_output_creates_parent_directory(tmp_path: Path):
    output = tmp_path / "new" / "nested" / "nexus.json"
    result = CliRunner().invoke(
        cli, ["evidence", "nexus", str(REPO_ROOT / "NEXUS"), "--output", str(output)]
    )
    assert result.exit_code == 0, result.output
    assert output.is_file()
