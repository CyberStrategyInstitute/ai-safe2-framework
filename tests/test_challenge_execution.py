from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from safe2.challenge.execution import create_plan, execute_plan, verify_execution
from safe2.challenge.integrity import digest, seal
from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.evidence.manifest import create_manifest

EXECUTOR = Path(__file__).parent / "fixtures" / "challenge_executor.py"


def _plan(**overrides):
    values = {
        "provider_name": "Acceptance executor", "provider_version": "1.0",
        "producer_id": "safe2-test-suite", "treatment": "external-reference",
    }
    values.update(overrides)
    return create_plan([sys.executable, str(EXECUTOR)], **values)


def test_controlled_execution_produces_bound_complete_evidence():
    plan = _plan()
    source, run, receipt = execute_plan(plan)
    assert validate_artifact("challenge-execution-plan-v1", plan) == []
    assert validate_artifact("challenge-source", source) == []
    assert validate_artifact("challenge-run", run) == []
    assert validate_artifact("challenge-execution-receipt-v1", receipt) == []
    assert run["summary"]["episodes"] == 6
    assert run["summary"]["status_counts"] == {"valid": 6, "incomplete": 0, "conflict": 0}
    assert receipt["source_sha256"] == digest(source)
    assert receipt["executor_unchanged"] is True
    assert receipt["claims"] == {
        "parent_process_bounded": True, "process_sandboxed": False,
        "descendant_containment": False,
        "independent_replication": "not_established",
    }
    assert verify_execution(plan, source, run, receipt)["valid"] is True


def test_invalid_executor_output_is_visible_as_incomplete(tmp_path: Path):
    bad = tmp_path / "bad.py"
    bad.write_text("print('not json')\n", encoding="utf-8")
    source, run, receipt = execute_plan(create_plan(
        [sys.executable, str(bad)], provider_name="bad", provider_version="1",
        producer_id="bad-fixture", treatment="bad-output",
    ))
    assert run["summary"]["status_counts"]["incomplete"] == 6
    assert {item["status"] for item in receipt["episode_receipts"]} == {"invalid_response"}
    assert all(item["observation"]["status"] == "missing" for item in source["episodes"])


def test_timeout_and_output_caps_are_visible_not_success():
    common = {
        "provider_name": "adversarial", "provider_version": "1",
        "producer_id": "adversarial-fixture", "treatment": "negative-control",
    }
    timeout_plan = create_plan(
        [sys.executable, "-c", "import time; time.sleep(2)"],
        timeout_seconds=0.1, **common,
    )
    _, timeout_run, timeout_receipt = execute_plan(timeout_plan)
    assert timeout_run["summary"]["status_counts"]["incomplete"] == 6
    assert {item["status"] for item in timeout_receipt["episode_receipts"]} == {"timeout"}

    output_plan = create_plan(
        [sys.executable, "-c", "print('x' * 2048)"], max_output_bytes=1024, **common,
    )
    _, output_run, output_receipt = execute_plan(output_plan)
    assert output_run["summary"]["status_counts"]["incomplete"] == 6
    assert {item["status"] for item in output_receipt["episode_receipts"]} == {"output_limit"}


def test_command_symlink_is_resolved_to_exact_regular_target(tmp_path: Path):
    target = tmp_path / "executor.py"
    target.write_text("print('not executed during planning')\n", encoding="utf-8")
    link = tmp_path / "executor-link.py"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("Host does not permit test symlinks")
    plan = create_plan(
        [sys.executable, str(link)], provider_name="link-test", provider_version="1",
        producer_id="link-test", treatment="link-test",
    )
    assert plan["command"][1] == str(target.resolve())
    assert plan["command_file_bindings"][1]["path"] == str(target.resolve())


def test_cli_requires_authorization_and_writes_new_bundle(tmp_path: Path):
    runner = CliRunner()
    plan_path = tmp_path / "plan.json"
    result = runner.invoke(cli, [
        "challenge", "plan", "001", "--executable", sys.executable,
        "--arg", str(EXECUTOR), "--provider-name", "CLI executor",
        "--provider-version", "1", "--producer-id", "cli-test",
        "--treatment", "external-reference", "--output", str(plan_path),
    ])
    assert result.exit_code == 0, result.output
    destination = tmp_path / "result"
    denied = runner.invoke(cli, ["challenge", "execute", str(plan_path), "--output-dir", str(destination)])
    assert denied.exit_code != 0
    assert not destination.exists()
    result = runner.invoke(cli, [
        "challenge", "execute", str(plan_path), "--output-dir", str(destination),
        "--authorize-process-execution",
    ])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["process_sandboxed"] is False
    assert {path.name for path in destination.iterdir()} == {
        "challenge-source.json", "challenge-run.json", "execution-receipt.json",
    }
    verified = runner.invoke(cli, [
        "challenge", "verify-execution", str(destination), "--plan", str(plan_path),
    ])
    assert verified.exit_code == 0, verified.output


def test_verifier_detects_cross_artifact_substitution():
    plan = _plan(seed=3)
    source, run, receipt = execute_plan(plan)
    other_plan = _plan(seed=4)
    result = verify_execution(other_plan, source, run, receipt)
    assert result["valid"] is False
    assert "plan_binding_mismatch" in result["errors"]

    tampered = copy.deepcopy(receipt)
    tampered["episode_receipts"][0]["status"] = "process_error"
    assert "receipt_integrity_mismatch" in verify_execution(plan, source, run, tampered)["errors"]

    forged = copy.deepcopy(receipt)
    forged["command_file_checks"][0]["unchanged"] = not forged["command_file_checks"][0]["unchanged"]
    forged = seal(forged)
    assert "command_file_binding_mismatch" in verify_execution(plan, source, run, forged)["errors"]


def test_execution_contracts_enter_evidence_manifest(tmp_path: Path):
    plan = _plan()
    source, run, receipt = execute_plan(plan)
    paths = []
    for name, artifact in (("plan.json", plan), ("source.json", source),
                           ("run.json", run), ("receipt.json", receipt)):
        path = tmp_path / name
        path.write_text(json.dumps(artifact), encoding="utf-8")
        paths.append(path)
    manifest = create_manifest(tuple(paths), subject_id="challenge-controlled-run")
    assert manifest["summary"] == {"artifacts": 4, "valid": 4, "invalid": 0}
