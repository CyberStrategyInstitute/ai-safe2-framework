from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from pathlib import Path

import pytest
from click.testing import CliRunner

from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.development.workflow import create_plan, create_receipt, verify_development_artifact


def _policy() -> dict:
    return json.loads(
        files("safe2.data").joinpath("development-policy-v1.json").read_text(encoding="utf-8")
    )


def _risk_policy() -> dict:
    return json.loads(
        (Path(__file__).parents[1] / ".ai-safe2" / "review-policy.json").read_text(
            encoding="utf-8"
        )
    )


def _source(**overrides: object) -> dict:
    source = {
        "schema_version": "safe2.development-plan-source.v1",
        "task_id": "task.bounded-change",
        "title": "Add bounded behavior",
        "outcome": "The CLI reports the requested bounded state.",
        "delivery_shape": "bounded",
        "risk_tier": "medium",
        "change_kind": "code",
        "work_product": "reusable",
        "acceptance_conditions": ["A failing test precedes the implementation."],
        "scope": {"include": ["safe2/example.py"], "exclude": ["release automation"]},
        "trust_boundaries": ["CLI input to local parser."],
        "assumptions": [],
        "unknowns": [],
        "design": {"summary": "Extend the existing command without a new service.", "approved": False},
        "isolation": {"strategy": "worktree", "reference": "feat/bounded-change"},
        "testing": {"mode": "tdd"},
    }
    source.update(overrides)
    return source


def _write_evidence(root: Path, evidence_ids: list[str]) -> list[dict[str, str]]:
    observations = []
    for evidence_id in evidence_ids:
        path = root / f"{evidence_id}.txt"
        payload = f"evidence:{evidence_id}\n".encode()
        path.write_bytes(payload)
        observations.append(
            {
                "evidence_id": evidence_id,
                "status": "passed",
                "artifact_path": path.name,
                "expected_sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return observations


def test_bounded_medium_plan_is_ready_and_tamper_evident():
    plan = create_plan(_source(), _policy())

    assert plan["disposition"] == "ready"
    assert plan["requirements"]["human_design_approval"] is False
    assert plan["requirements"]["review_cadence"] == "subsystem"
    assert plan["authorization"] == {
        "merge": False,
        "release": False,
        "deploy": False,
        "exception": False,
        "policy_change": False,
    }
    assert validate_artifact("development-plan-v1", plan) == []
    assert verify_development_artifact(plan)["valid"] is True

    plan["task"]["outcome"] = "tampered"
    assert verify_development_artifact(plan)["integrity"] == "invalid"


def test_critical_architecture_names_missing_decisions():
    source = _source(
        delivery_shape="architectural",
        risk_tier="critical",
        design={"summary": "Change an authorization boundary.", "approved": False},
        testing={"mode": "contract-first"},
    )
    plan = create_plan(source, _policy())

    assert plan["disposition"] == "review_required"
    assert {item["code"] for item in plan["gaps"]} == {
        "design_approval_missing",
        "design_approval_reference_missing",
        "design_artifact_missing",
        "threat_model_missing",
    }
    assert plan["requirements"]["greptile_recommended"] is True


def test_repository_path_policy_can_raise_but_not_lower_risk():
    source = _source(
        risk_tier="medium",
        scope={"include": ["safe2/commands/dev.py"], "exclude": []},
    )
    plan = create_plan(source, _policy(), _risk_policy())

    assert plan["task"]["declared_risk_tier"] == "medium"
    assert plan["task"]["risk_tier"] == "critical"
    assert plan["risk_classification"]["risk_raised"] is True
    assert [item["id"] for item in plan["risk_classification"]["matched_rules"]] == [
        "release-and-supply-chain"
    ]
    assert plan["requirements"]["threat_model"] is True
    assert plan["requirements"]["greptile_recommended"] is True
    assert plan["requirements"]["specialist_review"] is True
    assert plan["requirements"]["rollback"] is True
    assert "installed-wheel" in plan["requirements"]["required_evidence"]
    assert "security-review" in plan["requirements"]["required_evidence"]
    assert "supply-chain" in plan["requirements"]["review_lenses"]
    assert plan["disposition"] == "review_required"


def test_spike_cannot_be_promoted_as_reusable_output():
    source = _source(
        delivery_shape="spike",
        risk_tier="low",
        work_product="reusable",
        testing={"mode": "approved-spike"},
    )
    plan = create_plan(source, _policy())

    assert plan["disposition"] == "invalid"
    assert [item["code"] for item in plan["gaps"]] == ["spike_reusable_conflict"]


def test_receipt_supports_hash_bound_evidence_without_granting_authority(tmp_path: Path):
    plan = create_plan(_source(), _policy())
    evidence_ids = plan["requirements"]["required_evidence"]
    source = {
        "schema_version": "safe2.development-receipt-source.v1",
        "receipt_id": "receipt.bounded-change",
        "task_id": plan["plan_id"],
        "revision": "abc1234",
        "evidence": _write_evidence(tmp_path, evidence_ids),
        "test_cycle": {
            "mode": "tdd",
            "red": {"status": "observed", "evidence_id": "red-state"},
            "green": {"status": "observed", "evidence_id": "green-state"},
        },
        "before_after": {"status": "not_applicable", "evidence_ids": []},
        "reviews": [],
        "open_findings": [],
        "residual_risks": [],
        "rollback": "Revert the bounded commit.",
        "completion_claim": "Acceptance conditions have evidence at this revision.",
    }

    receipt = create_receipt(plan, source, tmp_path)

    assert receipt["claim_status"] == "supported"
    assert all(item["status"] == "supported" for item in receipt["required_evidence"])
    assert receipt["authorization"]["completion"] is False
    assert receipt["authorization"]["merge"] is False
    assert validate_artifact("development-receipt-v1", receipt) == []


def test_receipt_rejects_artifact_path_escape(tmp_path: Path):
    plan = create_plan(_source(), _policy())
    source = {
        "schema_version": "safe2.development-receipt-source.v1",
        "receipt_id": "receipt.path-escape",
        "task_id": plan["plan_id"],
        "revision": "abc1234",
        "evidence": [
            {
                "evidence_id": "red-state",
                "status": "passed",
                "artifact_path": "../outside.txt",
                "expected_sha256": "0" * 64,
            }
        ],
        "test_cycle": {
            "mode": "tdd",
            "red": {"status": "observed", "evidence_id": "red-state"},
            "green": {"status": "not_observed"},
        },
        "before_after": {"status": "not_applicable", "evidence_ids": []},
        "reviews": [],
        "open_findings": [],
        "residual_risks": [],
        "completion_claim": "This must remain unverifiable.",
    }

    receipt = create_receipt(plan, source, tmp_path)

    assert receipt["claim_status"] == "review_required"
    red = next(item for item in receipt["required_evidence"] if item["evidence_id"] == "red-state")
    assert red["reason"] == "artifact_unavailable_or_unsafe"


def test_independent_review_status_without_bound_evidence_is_not_supported(tmp_path: Path):
    plan = create_plan(
        _source(
            delivery_shape="architectural",
            risk_tier="low",
            design={
                "summary": "Change a durable parser boundary.",
                "artifact": "docs/design.md",
                "approved": True,
                "approval_reference": "issue:approved",
            },
        ),
        _policy(),
    )
    evidence_ids = plan["requirements"]["required_evidence"] + [
        "before-state",
        "after-state",
    ]
    source = {
        "schema_version": "safe2.development-receipt-source.v1",
        "receipt_id": "receipt.unbound-review",
        "task_id": plan["plan_id"],
        "revision": "abc1234",
        "evidence": _write_evidence(tmp_path, evidence_ids),
        "test_cycle": {
            "mode": "tdd",
            "red": {"status": "observed", "evidence_id": "red-state"},
            "green": {"status": "observed", "evidence_id": "green-state"},
        },
        "before_after": {
            "status": "compared",
            "evidence_ids": ["before-state", "after-state"],
        },
        "reviews": [{"kind": "human", "status": "completed"}],
        "open_findings": [],
        "residual_risks": [],
        "rollback": "Revert the architectural commit.",
        "completion_claim": "The change has evidence but the review is not bound.",
    }

    receipt = create_receipt(plan, source, tmp_path)

    assert receipt["claim_status"] == "review_required"
    independent = next(
        item for item in receipt["process_checks"] if item["id"] == "independent-review"
    )
    assert independent["reason"] == "human_review_missing"


def test_development_replay_corpus_is_green(tmp_path: Path):
    output = tmp_path / "replay.json"
    corpus = Path(__file__).parents[1] / ".ai-safe2" / "development-evals"
    result = CliRunner().invoke(
        cli,
        [
            "dev",
            "replay",
            str(corpus),
            "--policy",
            str(Path(__file__).parents[1] / ".ai-safe2" / "development-policy.json"),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["total"] == 4
    assert report["failed"] == 0
    assert report["model_evaluated"] is False


def test_repository_policy_matches_packaged_default():
    repository_policy = json.loads(
        (Path(__file__).parents[1] / ".ai-safe2" / "development-policy.json").read_text(
            encoding="utf-8"
        )
    )
    assert repository_policy == _policy()


def test_invalid_source_is_rejected_without_echoing_values():
    source = _source()
    source["secret_field"] = "DO_NOT_ECHO"
    with pytest.raises(ValueError, match="failed structural validation") as error:
        create_plan(source, _policy())
    assert "DO_NOT_ECHO" not in str(error.value)


def test_scope_paths_must_remain_repository_relative():
    source = _source(scope={"include": ["../safe2/commands/dev.py"], "exclude": []})
    with pytest.raises(ValueError, match="repository-relative"):
        create_plan(source, _policy(), _risk_policy())


def test_skill_workflow_uses_unified_gate_and_retains_report():
    root = Path(__file__).parents[1]
    workflow = (root / ".github" / "workflows" / "skill-trust-gate.yml").read_text(
        encoding="utf-8"
    )
    assert "python -m safe2 gate skill" in workflow
    assert "python scripts/skill_trust_gate.py" not in workflow
    assert "trust-gate-*.txt" in workflow
    assert "python -m pip install ." in workflow
