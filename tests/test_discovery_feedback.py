from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from jsonschema import Draft202012Validator

from safe2.cli import cli
from safe2.discovery.local import discover_local
from safe2.evidence.friction import append_event, record_event, summarize_events, verify_event


def test_discovery_detects_project_harness_without_reading_contents(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text("SECRET_SENTINEL", encoding="utf-8")
    result = discover_local(tmp_path, include_wsl=False)
    codex = next(row for row in result["harnesses"] if row["id"] == "codex")
    assert codex["detected"] is True
    assert result["privacy"]["configuration_contents_collected"] is False
    assert "SECRET_SENTINEL" not in json.dumps(result)


def test_doctor_json_has_stable_inventory_contract(tmp_path: Path):
    (tmp_path / "CLAUDE.md").write_text("# policy", encoding="utf-8")
    result = CliRunner().invoke(cli, ["doctor", str(tmp_path), "--no-wsl", "--format", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == "safe2.discovery.v1"
    assert any(row["id"] == "claude-code" for row in payload["harnesses"])
    assert payload["summary"]["assessment_status"] == "inventory_only"
    assert payload["integrity"]["authenticity"] == "unsigned"
    assert len(payload["integrity"]["digest"]) == 64


def test_doctor_human_output_exposes_integrity_without_claiming_authenticity(tmp_path: Path):
    result = CliRunner().invoke(cli, ["doctor", str(tmp_path), "--no-wsl"])
    assert result.exit_code == 0, result.output
    assert "Evidence integrity: sha256:" in result.output
    assert "(unsigned)" in result.output


def test_doctor_assess_keeps_inventory_and_posture_scopes_separate(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text("# policy", encoding="utf-8")
    result = CliRunner().invoke(
        cli, ["doctor", str(tmp_path), "--no-wsl", "--assess", "--format", "json"]
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["summary"]["assessment_status"] == "inventory_only"
    assert payload["posture"]["schema_version"] == "safe2.environment-posture.v1"
    assert payload["posture"]["coverage"]["configuration_contents_assessed"] is False
    assert payload["posture"]["coverage"]["configuration_inspection_requested"] is False


def test_doctor_compares_with_written_baseline(tmp_path: Path):
    baseline_path = tmp_path / "baseline.json"
    runner = CliRunner()
    baseline = runner.invoke(
        cli,
        [
            "doctor",
            str(tmp_path),
            "--no-wsl",
            "--inspect-config",
            "--output",
            str(baseline_path),
            "--format",
            "json",
        ],
    )
    assert baseline.exit_code == 0, baseline.output

    current = runner.invoke(
        cli,
        [
            "doctor",
            str(tmp_path),
            "--no-wsl",
            "--inspect-config",
            "--baseline",
            str(baseline_path),
            "--assess",
            "--format",
            "json",
        ],
    )
    assert current.exit_code == 0, current.output
    payload = json.loads(current.output)
    assert payload["drift"]["schema_version"] == "safe2.discovery-drift.v1"
    assert payload["drift"]["scope_changed"] is False
    assert payload["drift"]["changes"] == 0
    assert payload["drift"]["baseline_integrity"] == "valid"
    assert payload["posture"]["coverage"]["baseline_comparison"] is True


def test_friction_summary_exposes_completion_evidence_gap(tmp_path: Path):
    path = tmp_path / "friction.jsonl"
    runner = CliRunner()
    common = ["feedback", "record", "--severity", "high", "--output", str(path)]
    first = runner.invoke(
        cli,
        common + ["--category", "false_completion", "--outcome", "unverified_done", "--summary", "Agent claimed a change without a diff."],
    )
    second = runner.invoke(
        cli,
        common + ["--category", "silent_tool_failure", "--outcome", "verified_done", "--summary", "Retry was verified.", "--evidence-ref", "test:passed"],
    )
    assert first.exit_code == second.exit_code == 0
    summary = summarize_events(path)
    assert summary["claimed_completion"] == 2
    assert summary["reference_attested_completion"] == 1
    assert summary["completion_evidence_gap"] == 1
    assert summary["evidence_attachment_rate"] == 0.5
    assert summary["integrity"]["sealed_events"] == 2
    assert summary["integrity"]["unsigned_events"] == 0
    assert summary["integrity"]["coverage"] == 1.0
    assert summary["by_severity"] == {"high": 2}
    assert summary["resolution"]["unresolved"] == 2
    assert summary["time_window"]["first_recorded_at"] is not None
    assert summary["top_categories"][0]["events"] == 1


def test_friction_event_does_not_claim_external_verification_without_evidence():
    event = record_event(
        category="missing_evidence",
        outcome="blocked",
        severity="medium",
        summary="Required result was unavailable.",
    )
    assert event["verification"] == "self_reported"
    assert event["evidence_count"] == 0
    assert len(event["integrity_sha256"]) == 64
    assert verify_event(event) == "valid"


def test_friction_summary_rejects_tampered_event(tmp_path: Path):
    path = tmp_path / "friction.jsonl"
    event = record_event(
        category="missing_evidence",
        outcome="blocked",
        severity="high",
        summary="Original sanitized observation.",
    )
    event["outcome"] = "verified_done"
    path.write_text(json.dumps(event) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="integrity verification failed on line 1"):
        summarize_events(path)


def test_friction_summary_labels_legacy_unsigned_events(tmp_path: Path):
    path = tmp_path / "friction.jsonl"
    event = record_event(
        category="context_loss",
        outcome="failed",
        severity="medium",
        summary="Legacy event.",
    )
    event.pop("integrity_sha256")
    path.write_text(json.dumps(event) + "\n", encoding="utf-8")
    summary = summarize_events(path)
    assert summary["integrity"]["sealed_events"] == 0
    assert summary["integrity"]["unsigned_events"] == 1
    assert summary["integrity"]["coverage"] == 0.0


def test_friction_summary_rejects_structurally_invalid_unsigned_event(tmp_path: Path):
    path = tmp_path / "friction.jsonl"
    event = record_event(
        category="context_loss",
        outcome="failed",
        severity="medium",
        summary="Legacy event.",
    )
    event.pop("integrity_sha256")
    event["category"] = "invented_category"
    path.write_text(json.dumps(event) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="contract violation on line 1"):
        summarize_events(path)


def test_friction_summary_rejects_inconsistent_evidence_semantics(tmp_path: Path):
    path = tmp_path / "friction.jsonl"
    event = record_event(
        category="missing_evidence",
        outcome="blocked",
        severity="high",
        summary="Evidence missing.",
    )
    event.pop("integrity_sha256")
    event["evidence_count"] = 3
    path.write_text(json.dumps(event) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="evidence_count mismatch on line 1"):
        summarize_events(path)


def test_feedback_summary_writes_manifest_ready_json(tmp_path: Path):
    source = tmp_path / "friction.jsonl"
    output = tmp_path / "friction-summary.json"
    append_event(
        source,
        record_event(
            category="permission_friction",
            outcome="blocked",
            severity="medium",
            summary="Approval was unavailable.",
        ),
    )
    result = CliRunner().invoke(
        cli, ["feedback", "summary", str(source), "--output", str(output)]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(output.read_text(encoding="utf-8"))["schema_version"] == (
        "safe2.friction-summary.v1"
    )


def test_friction_log_symlinks_and_size_limits_fail_closed(tmp_path: Path):
    target = tmp_path / "target.jsonl"
    target.write_text("", encoding="utf-8")
    link = tmp_path / "link.jsonl"
    try:
        link.symlink_to(target)
    except OSError:
        return
    event = record_event(
        category="integration_failure",
        outcome="failed",
        severity="high",
        summary="Integration failed.",
    )
    with pytest.raises(ValueError, match="symbolic link"):
        append_event(link, event)
    with pytest.raises(ValueError, match="symbolic link"):
        summarize_events(link)

    oversized = tmp_path / "oversized.jsonl"
    oversized.write_text(json.dumps(event) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="maximum supported size"):
        summarize_events(oversized, max_bytes=1)


def test_verified_done_requires_external_evidence():
    with pytest.raises(ValueError, match="requires at least one"):
        record_event(
            category="false_completion",
            outcome="verified_done",
            severity="high",
            summary="This must not be accepted on self-report alone.",
        )


def test_evidence_reference_must_be_structured_and_bounded():
    with pytest.raises(ValueError, match="scheme:value"):
        record_event(
            category="false_completion",
            outcome="verified_done",
            severity="high",
            summary="Unstructured evidence must not count.",
            evidence_refs=("x",),
        )


def test_friction_event_matches_published_schema():
    event = record_event(
        category="silent_tool_failure",
        outcome="verified_done",
        severity="high",
        summary="The retry produced a verified state change.",
        evidence_refs=("sha256:example",),
    )
    schema_path = Path(__file__).resolve().parent.parent / "safe2" / "data" / "friction-event-v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(event)
