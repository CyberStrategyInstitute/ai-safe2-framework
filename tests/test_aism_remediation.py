from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from safe2.aism.remediation import build, render_markdown
from safe2.cli import cli
from safe2.evidence.scope import build as build_scope
from safe2.evidence.system_identity import ingest as ingest_identity

ROOT = Path(__file__).resolve().parent.parent


def encoded(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True) + "\n").encode()


def artifacts() -> tuple[bytes, bytes, bytes]:
    assessment = json.loads((ROOT / "examples/aism-decision-card/assessment.json").read_text())
    assessment["subject"]["id"] = "demo-agent-system"
    assessment["conflicts"] = []
    assessment_data = encoded(assessment)
    identity = ingest_identity((ROOT / "safe2/data/system-identity-source-demo.json").read_bytes())
    identity_data = encoded(identity)
    scope = build_scope(
        (ROOT / "safe2/data/assessment-scope-source-demo.json").read_bytes(),
        identity_data,
        ROOT,
    )
    return assessment_data, identity_data, encoded(scope)


def source(assessment: bytes, identity: bytes, scope: bytes) -> dict:
    return {
        "schema_version": "safe2.aism-remediation-source.v1",
        "plan_id": "demo-remediation-1",
        "subject_id": "demo-agent-system",
        "decision_owner": "Accountable system owner",
        "bindings": {
            "assessment_sha256": hashlib.sha256(assessment).hexdigest(),
            "system_identity_sha256": hashlib.sha256(identity).hexdigest(),
            "assessment_scope_sha256": hashlib.sha256(scope).hexdigest(),
        },
        "assumptions": [
            {
                "id": "REMEDIATION-ASSUMPTION-1",
                "statement": "The test boundary represents the proposed deployment.",
                "effect_if_false": "The action must be rescoped.",
            }
        ],
        "alternatives": [
            {
                "id": "ALT-1",
                "name": "Retain read-only operation",
                "pros": ["Immediately reversible"],
                "cons": ["Reduced automation"],
                "reason_not_selected": "Use only as containment while the control is repaired.",
            }
        ],
        "actions": [
            {
                "id": "ACTION-1",
                "sequence": 1,
                "title": "Repair fail-closed authorization",
                "description": "Correct and retest the policy-service interruption path.",
                "status": "planned",
                "priority": "critical",
                "owner": "Platform engineering",
                "control_refs": ["P3.T5.1"],
                "aism_cells": ["P3.D3"],
                "evidence_refs": ["FACT-001"],
                "assumption_refs": ["ASSUMPTION-001"],
                "dependencies": [],
                "alternative_refs": ["ALT-1"],
                "impacts": [
                    {
                        "perspective": "ciso",
                        "statement": "Restores the declared authority boundary.",
                    },
                    {
                        "perspective": "engineering",
                        "statement": "Requires interruption-path tests.",
                    },
                    {
                        "perspective": "governance",
                        "statement": "Produces evidence for a new review.",
                    },
                    {"perspective": "agent", "statement": "Write authority remains constrained."},
                ],
                "why": "Runtime evidence showed the fail-closed path is the limiting control.",
                "why_not": "Do not enable writes before the exit criteria are evidenced.",
                "exit_criteria": ["Interruption tests deny every unauthorized write."],
                "completion_evidence_refs": [],
                "residual_risk": "A different untested outage mode may remain.",
                "residual_risk_ref": None,
            }
        ],
        "accepted_residual_risks": [],
    }


def test_plan_binds_identity_scope_and_keeps_normative_score_separate():
    assessment, identity, scope = artifacts()
    plan = build(encoded(source(assessment, identity, scope)), assessment, identity, scope)
    assert plan["bindings"]["system_fingerprint_sha256"]
    assert plan["assessment"]["normative_score_unchanged"] is True
    assert plan["assumptions"][0]["id"] == "REMEDIATION-ASSUMPTION-1"
    assert plan["decision"] == {
        "gate": "hold",
        "reason": "A scope, conflict, dependency, or completion-regression blocker requires human resolution.",
        "human_owned": True,
        "remediation_authorized": False,
        "conformance_claim": False,
    }
    assert plan["summary"]["uncovered_gaps"] > 0
    card = render_markdown(plan)
    assert "## Recommended sequence" in card
    assert "Remediation authorized: **false**" in card
    assert "Why not" in card
    assert "## Assumptions" in card


def test_binding_change_is_rejected():
    assessment, identity, scope = artifacts()
    value = source(assessment, identity, scope)
    value["bindings"]["assessment_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="bindings do not match"):
        build(encoded(value), assessment, identity, scope)


def test_unknown_traceability_and_dependency_cycles_are_rejected():
    assessment, identity, scope = artifacts()
    value = source(assessment, identity, scope)
    value["actions"][0]["control_refs"] = ["P9.T9.9"]
    with pytest.raises(ValueError, match="unknown AI SAFE2 control"):
        build(encoded(value), assessment, identity, scope)
    value = source(assessment, identity, scope)
    value["actions"][0]["dependencies"] = ["ACTION-1"]
    with pytest.raises(ValueError, match="cannot depend on itself"):
        build(encoded(value), assessment, identity, scope)


def test_dependency_sequence_and_duplicate_governance_ids_are_rejected():
    assessment, identity, scope = artifacts()
    value = source(assessment, identity, scope)
    first = value["actions"][0]
    first["dependencies"] = ["ACTION-2"]
    second = dict(first)
    second.update({"id": "ACTION-2", "sequence": 2, "dependencies": []})
    value["actions"] = [first, second]
    with pytest.raises(ValueError, match="earlier sequence"):
        build(encoded(value), assessment, identity, scope)
    value = source(assessment, identity, scope)
    value["alternatives"].append(dict(value["alternatives"][0]))
    with pytest.raises(ValueError, match="alternative identifiers"):
        build(encoded(value), assessment, identity, scope)


def test_accepted_risk_requires_declared_evidence_bound_risk():
    assessment, identity, scope = artifacts()
    value = source(assessment, identity, scope)
    value["actions"][0].update({"status": "accepted_risk", "residual_risk_ref": "RISK-1"})
    with pytest.raises(ValueError, match="requires a declared residual risk"):
        build(encoded(value), assessment, identity, scope)
    value["accepted_residual_risks"] = [
        {
            "id": "RISK-1",
            "statement": "An outage mode may remain.",
            "owner": "CISO",
            "rationale": "Temporary acceptance pending a scheduled control replacement.",
            "review_date": "2026-12-01",
            "evidence_refs": ["missing-evidence"],
        }
    ]
    with pytest.raises(ValueError, match="cites unavailable evidence"):
        build(encoded(value), assessment, identity, scope)


def test_completed_action_requires_available_completion_evidence():
    assessment, identity, scope = artifacts()
    value = source(assessment, identity, scope)
    value["actions"][0]["status"] = "completed"
    with pytest.raises(ValueError, match="requires completion evidence"):
        build(encoded(value), assessment, identity, scope)
    value["actions"][0]["completion_evidence_refs"] = ["missing-evidence"]
    with pytest.raises(ValueError, match="unavailable completion evidence"):
        build(encoded(value), assessment, identity, scope)


def test_previous_completion_regression_holds():
    assessment, identity, scope = artifacts()
    prior_source = source(assessment, identity, scope)
    prior_source["actions"][0]["status"] = "completed"
    prior_source["actions"][0]["completion_evidence_refs"] = ["FACT-001"]
    previous = build(encoded(prior_source), assessment, identity, scope)
    current = build(
        encoded(source(assessment, identity, scope)), assessment, identity, scope, encoded(previous)
    )
    assert current["decision"]["gate"] == "hold"
    assert current["history"][-1]["from"] == "completed"
    assert current["history"][-1]["to"] == "planned"


def test_cli_init_and_plan_preserve_outputs_before_strict_exit(tmp_path: Path):
    assessment, identity, scope = artifacts()
    assessment_path, identity_path, scope_path = (
        tmp_path / "assessment.json",
        tmp_path / "identity.json",
        tmp_path / "scope.json",
    )
    assessment_path.write_bytes(assessment)
    identity_path.write_bytes(identity)
    scope_path.write_bytes(scope)
    source_path = tmp_path / "source.json"
    runner = CliRunner()
    initialized = runner.invoke(
        cli,
        [
            "aism",
            "remediation-init",
            str(assessment_path),
            "--system-identity",
            str(identity_path),
            "--assessment-scope",
            str(scope_path),
            "--decision-owner",
            "CISO",
            "--output",
            str(source_path),
        ],
    )
    assert initialized.exit_code == 0, initialized.output
    template = json.loads(source_path.read_text())
    template.update(source(assessment, identity, scope))
    source_path.unlink()
    source_path.write_bytes(encoded(template))
    output, card = tmp_path / "plan.json", tmp_path / "plan.md"
    planned = runner.invoke(
        cli,
        [
            "aism",
            "plan",
            str(source_path),
            str(assessment_path),
            "--system-identity",
            str(identity_path),
            "--assessment-scope",
            str(scope_path),
            "--output",
            str(output),
            "--card",
            str(card),
            "--strict",
        ],
    )
    assert planned.exit_code == 1, planned.output
    assert output.exists() and card.exists()
    assert json.loads(output.read_text())["decision"]["gate"] == "hold"


def test_packaged_remediation_example_is_verifiable():
    result = CliRunner().invoke(cli, ["example", "verify", "aism-remediation"])
    assert result.exit_code == 0, result.output
    assert '"gate": "ready_for_human_decision"' in result.output
