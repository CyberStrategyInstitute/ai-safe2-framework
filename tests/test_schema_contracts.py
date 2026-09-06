from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

from click.testing import CliRunner
from jsonschema import Draft202012Validator

from safe2.cli import cli
from safe2.discovery.drift import compare_discovery
from safe2.discovery.integrity import seal_inventory
from safe2.discovery.posture import assess_posture
from safe2.evidence.friction import append_event, record_event, summarize_events


def _schema(name: str) -> dict[str, object]:
    content = files("safe2.data").joinpath(name).read_text(encoding="utf-8")
    return json.loads(content)


def _inventory(root: Path) -> dict[str, object]:
    return {
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


def test_all_packaged_schemas_are_valid_draft_2020_12():
    for name in (
        "aism-assessment-v1.schema.json",
        "discovery-v1.schema.json",
        "discovery-drift-v1.schema.json",
        "environment-posture-v1.schema.json",
        "environment-policy-v1.schema.json",
        "environment-policy-decision-v1.schema.json",
        "friction-event-v1.schema.json",
        "friction-summary-v1.schema.json",
        "run-manifest-v1.schema.json",
        "nexus-evidence-v1.schema.json",
        "skillspector-evidence-v1.schema.json",
    ):
        Draft202012Validator.check_schema(_schema(name))


def test_published_discovery_drift_and_posture_contracts(tmp_path: Path):
    baseline = _inventory(tmp_path)
    current = _inventory(tmp_path)
    drift = compare_discovery(current, baseline)
    current["drift"] = drift
    posture = assess_posture(current)
    current["posture"] = posture
    seal_inventory(current)

    Draft202012Validator(_schema("discovery-drift-v1.schema.json")).validate(drift)
    Draft202012Validator(_schema("environment-posture-v1.schema.json")).validate(posture)
    # Validate the top-level discovery contract without resolving its already
    # independently validated optional nested contracts.
    discovery = dict(current)
    discovery.pop("drift")
    discovery.pop("posture")
    seal_inventory(discovery)
    Draft202012Validator(_schema("discovery-v1.schema.json")).validate(discovery)


def test_published_friction_summary_contract(tmp_path: Path):
    source = tmp_path / "friction.jsonl"
    append_event(
        source,
        record_event(
            category="context_loss",
            outcome="blocked",
            severity="medium",
            summary="Context boundary required recovery.",
        ),
    )
    summary = summarize_events(source)
    Draft202012Validator(_schema("friction-summary-v1.schema.json")).validate(summary)


def test_schema_catalog_lists_and_exports_packaged_contracts(tmp_path: Path):
    runner = CliRunner()
    listed = runner.invoke(cli, ["schema", "list"])
    assert listed.exit_code == 0, listed.output
    catalog = json.loads(listed.output)
    assert "discovery-v1" in catalog["schemas"]
    assert "friction-summary-v1" in catalog["schemas"]

    output = tmp_path / "schema.json"
    exported = runner.invoke(
        cli, ["schema", "export", "environment-posture-v1", "--output", str(output)]
    )
    assert exported.exit_code == 0, exported.output
    assert json.loads(output.read_text(encoding="utf-8"))["title"] == (
        "AI SAFE2 Environment Posture"
    )


def test_schema_validate_has_stable_agent_exit_contract(tmp_path: Path):
    runner = CliRunner()
    valid_path = tmp_path / "valid.json"
    valid_path.write_text(json.dumps(seal_inventory(_inventory(tmp_path))), encoding="utf-8")
    valid = runner.invoke(cli, ["schema", "validate", "discovery-v1", str(valid_path)])
    assert valid.exit_code == 0, valid.output
    valid_result = json.loads(valid.output)
    assert valid_result["valid"] is True
    assert valid_result["error_count"] == 0

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text(json.dumps({"schema_version": "wrong"}), encoding="utf-8")
    invalid = runner.invoke(cli, ["schema", "validate", "discovery-v1", str(invalid_path)])
    assert invalid.exit_code == 1, invalid.output
    invalid_result = json.loads(invalid.output)
    assert invalid_result["valid"] is False
    assert invalid_result["error_count"] > 0
    assert invalid_result["privacy"]["instance_values_emitted"] is False
    assert all("message" not in error for error in invalid_result["errors"])


def test_schema_validate_uses_exit_two_for_unreadable_input(tmp_path: Path):
    source = tmp_path / "malformed.json"
    source.write_text('{"secret": "DO_NOT_ECHO"', encoding="utf-8")
    result = CliRunner().invoke(
        cli, ["schema", "validate", "friction-event-v1", str(source)]
    )
    assert result.exit_code == 2
    assert "DO_NOT_ECHO" not in result.output
    assert json.loads(result.output)["error"] == "JSONDecodeError"
