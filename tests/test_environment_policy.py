from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from jsonschema import Draft202012Validator

from safe2.cli import cli
from safe2.contracts import schema_text
from safe2.discovery.policy import evaluate_policy, load_policy
from safe2.discovery.posture import assess_posture


def _discovery(root: Path):
    result = {
        "schema_version": "safe2.discovery.v1",
        "scope": {"type": "local", "root": str(root)},
        "harnesses": [{"id": "codex", "commands": [], "evidence": []}],
        "targets": [],
        "asset_inventory": {"assets": [], "counts": {}, "truncated": False},
    }
    result["posture"] = assess_posture(result)
    return result


def _policy(**rules):
    return {"schema_version": "safe2.environment-policy.v1", "id": "ci-default", **rules}


def test_policy_distinguishes_allow_hold_and_deny(tmp_path: Path):
    discovery = _discovery(tmp_path)
    allowed = evaluate_policy(discovery, _policy(allowed_dispositions=["REVIEW"]))
    assert allowed["disposition"] == "ALLOW"
    assert allowed["exit_code"] == 0

    held = evaluate_policy(discovery, _policy(require_baseline=True))
    assert held["disposition"] == "HOLD"
    assert held["exit_code"] == 2
    assert held["unmet_prerequisites"][0]["rule"] == "require_baseline"

    denied = evaluate_policy(discovery, _policy(max_findings={"medium": 0}))
    assert denied["disposition"] == "DENY"
    assert denied["exit_code"] == 1
    assert denied["violations"][0]["rule"] == "max_findings.medium"

    schema = json.loads(schema_text("environment-policy-decision-v1"))
    Draft202012Validator(schema).validate(denied)


def test_policy_loader_rejects_unknown_rules_and_symlinks(tmp_path: Path):
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(_policy(invented_rule=True)), encoding="utf-8")
    with pytest.raises(ValueError, match="policy contract violation"):
        load_policy(path)
    link = tmp_path / "policy-link.json"
    try:
        link.symlink_to(path)
    except OSError:
        return
    with pytest.raises(ValueError, match="symbolic link"):
        load_policy(link)


def test_high_coverage_gap_cannot_fail_open_as_allow(tmp_path: Path):
    discovery = _discovery(tmp_path)
    discovery["posture"]["findings"].append(
        {
            "id": "COVERAGE-TRUNCATED",
            "severity": "high",
            "category": "coverage_gap",
            "title": "Coverage truncated",
            "facts": [],
            "assumptions": [],
            "recommendation": "Collect complete evidence.",
            "candidate_controls": ["P2"],
            "verification": "derived_from_discovery",
        }
    )
    result = evaluate_policy(discovery, _policy(allowed_dispositions=["REVIEW"]))
    assert result["disposition"] == "HOLD"
    assert result["unmet_prerequisites"][0]["rule"] == "decision_coverage_complete"


@pytest.mark.parametrize(
    ("policy", "expected_exit", "expected_disposition"),
    [
        (_policy(allowed_dispositions=["BASELINE"]), 0, "ALLOW"),
        (_policy(require_baseline=True), 2, "HOLD"),
        (_policy(allowed_dispositions=["REVIEW"]), 1, "DENY"),
    ],
)
def test_doctor_policy_enforcement_writes_evidence_before_exit(
    tmp_path: Path, monkeypatch, policy: dict, expected_exit: int, expected_disposition: str
):
    isolated_home = tmp_path / "empty-home"
    isolated_home.mkdir()
    monkeypatch.setattr("safe2.discovery.local.Path.home", lambda: isolated_home)
    monkeypatch.setattr("safe2.discovery.local.shutil.which", lambda _: None)
    policy_path = tmp_path / "policy.json"
    output = tmp_path / "result.json"
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    result = CliRunner().invoke(
        cli,
        [
            "doctor",
            str(tmp_path),
            "--no-wsl",
            "--assess",
            "--policy",
            str(policy_path),
            "--enforce-policy",
            "--output",
            str(output),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == expected_exit, result.output
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["policy_decision"]["disposition"] == expected_disposition
    assert payload["policy_decision"]["exit_code"] == expected_exit
