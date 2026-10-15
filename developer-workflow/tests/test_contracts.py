from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = ROOT / "scripts" / "validate_workflow.py"
    spec = importlib.util.spec_from_file_location("validate_workflow", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def decision_record():
    return {
        "schema_version": "ai-safe2.decision-record.v1",
        "decision_id": "pr-1@abc123",
        "subject": {"identifier": "pr-1", "revision": "abc123"},
        "route": "enhanced",
        "outcome": "hold",
        "required_evidence": ["targeted-validation", "semantic-review"],
        "evidence": [],
        "risks": [],
        "human_authority": {"required": True, "decision_owner": None, "decision_at": None, "rationale": None},
        "replay": {"policy_digest": "sha256:policy", "configuration_digest": "sha256:config", "producer_versions": {}},
    }


def ci_observation():
    return {
        "schema_version": "ai-safe2.ci-execution-observation.v1",
        "receipt_id": "ci-pr-44@abc123",
        "subject": {
            "identifier": "pr-44",
            "revision": "abc123",
            "capability": "device-privacy-tests",
        },
        "runner": {
            "provider": "github-actions",
            "image": "ubuntu-24.04",
            "operating_system": "Linux",
            "architecture": "x86_64",
            "environment_facts": {"hardware_acceleration": True, "api_level": 36},
        },
        "required_phases": ["environment_preflight", "build", "test", "postprocess"],
        "phases": [
            {"name": name, "status": "passed", "exit_code": 0, "failure_class": None, "failure_reason": None}
            for name in ("environment_preflight", "build", "test", "postprocess")
        ],
        "test_results": {
            "status": "passed",
            "minimum_required": 1,
            "discovered": 128,
            "executed": 128,
            "passed": 128,
            "failed": 0,
            "skipped": 0,
        },
        "artifacts": [{"name": "device-test-report", "digest": "sha256:example"}],
        "limitations": [],
    }


def test_package_contracts_validate():
    module = load_validator()
    assert module.validate_package(ROOT) == []


def test_adapters_cannot_authorize():
    manifests = json.loads((ROOT / "adapters" / "manifests.json").read_text(encoding="utf-8"))
    assert manifests
    assert all("authorize" not in manifest["authority"] for manifest in manifests)


def test_game_profile_contains_authority_and_economy_lenses():
    profile = json.loads((ROOT / "profiles" / "game.json").read_text(encoding="utf-8"))
    assert "client-server-authority" in profile["lenses"]
    assert "economy-inventory-purchase-entitlements" in profile["lenses"]


def test_required_provider_failure_cannot_be_pass():
    workflow = json.loads(
        (ROOT / "repository-template" / ".ai-safe2" / "workflow.json").read_text(encoding="utf-8")
    )
    assert workflow["invariants"]["provider_failure_is_not_pass"] is True
    assert workflow["routes"]["critical"]["security_review"] == "required"


def test_game_change_routing():
    path = ROOT / "scripts" / "classify_change.py"
    spec = importlib.util.spec_from_file_location("classify_change", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    profile = json.loads((ROOT / "profiles" / "game.json").read_text(encoding="utf-8"))
    assert module.classify(["docs/guide.md"], profile)["route"] == "standard"
    assert module.classify(["src/gameplay/player.cs"], profile)["route"] == "enhanced"
    assert module.classify(["src/multiplayer/authority.cs"], profile)["route"] == "critical"


def test_terminal_decision_requires_human_record():
    schema = json.loads((ROOT / "schemas" / "decision-record-v1.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    record = decision_record()
    record["outcome"] = "approved"
    with pytest.raises(ValidationError):
        validator.validate(record)
    record["human_authority"] = {
        "required": True,
        "decision_owner": "release-owner",
        "decision_at": "2026-10-09T04:00:00Z",
        "rationale": "Required evidence was reviewed.",
    }
    validator.validate(record)


def test_evidence_evaluator_is_revision_bound_and_cannot_authorize():
    module = load_script("evaluate_decision.py")
    record = decision_record()
    record["evidence"] = [
        {"evidence_id": "e1", "capability": "targeted-validation", "status": "produced", "subject_revision": "abc123", "producer": "pytest"},
        {"evidence_id": "e2", "capability": "semantic-review", "status": "produced", "subject_revision": "old-revision", "producer": "reviewer"},
    ]
    assert module.evaluate(record)["outcome"] == "hold"
    record["evidence"][1]["subject_revision"] = "abc123"
    evaluated = module.evaluate(record)
    assert evaluated["outcome"] == "ready_for_human_decision"
    assert evaluated["human_authority"]["decision_owner"] is None


def test_failed_or_unavailable_evidence_never_satisfies_requirement():
    module = load_script("evaluate_decision.py")
    record = decision_record()
    record["evidence"] = [
        {"evidence_id": "e1", "capability": capability, "status": status, "subject_revision": "abc123", "producer": "provider"}
        for capability, status in (("targeted-validation", "failed"), ("semantic-review", "unavailable"))
    ]
    assert module.evaluate(record)["outcome"] == "hold"


def test_template_classifier_matches_release_classifier(tmp_path):
    paths_file = tmp_path / "paths.txt"
    paths_file.write_text("docs/guide.md\nsrc/multiplayer/authority.cs\n", encoding="utf-8")
    outputs = []
    for script in (ROOT / "scripts" / "classify_change.py", ROOT / "repository-template" / "scripts" / "classify_change.py"):
        output = tmp_path / f"{script.parent.name}.json"
        subprocess.run(
            [sys.executable, str(script), "--profile", str(ROOT / "profiles" / "game.json"), "--paths-file", str(paths_file), "--output", str(output)],
            check=True,
        )
        outputs.append(json.loads(output.read_text(encoding="utf-8")))
    assert outputs[0] == outputs[1]
    assert outputs[0]["route"] == "critical"


def test_template_explainer_matches_release_and_describes_boundaries(tmp_path):
    workflow = ROOT / "repository-template" / ".ai-safe2" / "workflow.json"
    profile = ROOT / "repository-template" / ".ai-safe2" / "profiles" / "game.json"
    outputs = []
    for script in (
        ROOT / "scripts" / "explain_workflow.py",
        ROOT / "repository-template" / "scripts" / "explain_workflow.py",
    ):
        output = tmp_path / f"{script.parent.name}-workflow.md"
        subprocess.run(
            [
                sys.executable,
                str(script),
                "--workflow",
                str(workflow),
                "--profile",
                str(profile),
                "--output",
                str(output),
            ],
            check=True,
        )
        outputs.append(output.read_text(encoding="utf-8"))
    assert outputs[0] == outputs[1]
    assert "## What changed" in outputs[0]
    assert "## Current preview boundary" in outputs[0]
    assert "## CI execution evidence boundary" in outputs[0]
    assert "wrapper exit code" in outputs[0]
    assert "Superpowers" in outputs[0]
    assert "Codex Security" in outputs[0]
    assert "cannot merge, release, deploy, or" in outputs[0]
    assert "a CLI decision-routing result, a human decision record" in outputs[0]


def test_required_decision_tools_match_template():
    for name in ("build_cli_decision_request.py", "build_decision_record.py", "evaluate_decision.py"):
        assert (ROOT / "scripts" / name).read_text(encoding="utf-8").rstrip() == (
            ROOT / "repository-template" / "scripts" / name
        ).read_text(encoding="utf-8").rstrip()
    assert json.loads((ROOT / "schemas" / "decision-record-v1.schema.json").read_text(encoding="utf-8")) == json.loads(
        (ROOT / "repository-template" / ".ai-safe2" / "schemas" / "decision-record-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )


def test_ci_execution_receipt_is_revision_bound_and_schema_valid():
    module = load_script("evaluate_ci_execution.py")
    receipt = module.evaluate(ci_observation())
    assert receipt["subject"]["revision"] == "abc123"
    assert receipt["outcome"] == "produced"
    assert receipt["failure"] == {"class": None, "phase": None, "reason": None}
    schema = json.loads((ROOT / "schemas" / "ci-execution-receipt-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(receipt)
    unsigned = {key: value for key, value in receipt.items() if key != "integrity"}
    assert receipt["integrity"]["content_digest"] == module.canonical_digest(unsigned)


def test_ci_environment_failure_is_not_an_application_failure():
    module = load_script("evaluate_ci_execution.py")
    source = ci_observation()
    source["phases"][0] = {
        "name": "environment_preflight",
        "status": "failed",
        "exit_code": 1,
        "failure_class": "environment_preflight",
        "failure_reason": "Required accelerator was unavailable.",
    }
    source["phases"][1]["status"] = "not_run"
    source["phases"][2]["status"] = "not_run"
    source["phases"][3]["status"] = "not_run"
    source["test_results"] = None
    receipt = module.evaluate(source)
    assert receipt["outcome"] == "failed"
    assert receipt["failure"]["class"] == "environment_preflight"
    assert receipt["failure"]["phase"] == "environment_preflight"


def test_ci_postprocess_failure_preserves_passing_test_result():
    module = load_script("evaluate_ci_execution.py")
    source = ci_observation()
    source["phases"][3] = {
        "name": "postprocess",
        "status": "failed",
        "exit_code": 2,
        "failure_class": "postprocess",
        "failure_reason": "The wrapper split a multiline shell conditional.",
    }
    receipt = module.evaluate(source)
    assert receipt["outcome"] == "failed"
    assert receipt["failure"]["class"] == "postprocess"
    assert receipt["test_results"]["status"] == "passed"
    assert receipt["test_results"]["executed"] == 128
    assert receipt["test_results"]["failed"] == 0


def test_ci_zero_or_inconsistent_tests_fail_closed_as_harness_failure():
    module = load_script("evaluate_ci_execution.py")
    source = ci_observation()
    source["test_results"].update(
        {"status": "passed", "discovered": 0, "executed": 0, "passed": 0}
    )
    receipt = module.evaluate(source)
    assert receipt["outcome"] == "failed"
    assert receipt["failure"]["class"] == "test_harness"
    assert receipt["failure"]["phase"] == "test"


def test_ci_rejects_internally_inconsistent_counts_and_non_scalar_runner_facts():
    module = load_script("evaluate_ci_execution.py")
    source = ci_observation()
    source["test_results"]["executed"] = 127
    with pytest.raises(ValueError, match="executed must equal"):
        module.evaluate(source)

    source = ci_observation()
    source["runner"]["environment_facts"]["nested"] = {"unexpected": True}
    with pytest.raises(ValueError, match="values must be scalar"):
        module.evaluate(source)

    source = ci_observation()
    source["test_results"]["executed"] = True
    with pytest.raises(ValueError, match="non-negative integers"):
        module.evaluate(source)


def test_ci_execution_contract_and_evaluator_match_repository_template():
    assert (ROOT / "scripts" / "evaluate_ci_execution.py").read_text(encoding="utf-8").rstrip() == (
        ROOT / "repository-template" / "scripts" / "evaluate_ci_execution.py"
    ).read_text(encoding="utf-8").rstrip()
    assert json.loads((ROOT / "schemas" / "ci-execution-receipt-v1.schema.json").read_text(encoding="utf-8")) == json.loads(
        (ROOT / "repository-template" / ".ai-safe2" / "schemas" / "ci-execution-receipt-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )


def test_setup_assistant_matches_template_and_is_goal_based():
    release = (ROOT / "scripts" / "setup_assistant.py").read_text(encoding="utf-8")
    template = (ROOT / "repository-template" / "scripts" / "setup_assistant.py").read_text(
        encoding="utf-8"
    )
    assert release.rstrip() == template.rstrip()
    module = load_script("setup_assistant.py")
    plan = module.render_plan({"planning", "semantic-review", "strategic-review"})
    assert "Required core — always install" in plan
    assert "Superpowers" in plan
    assert "OPENROUTER_API_KEY" in plan
    assert "Greptile" in plan
    assert "does not install a" in plan
    assert "named human" in plan


def test_tool_setup_guide_is_linked_and_preserves_integration_boundaries():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    guide = (ROOT / "docs" / "TOOL-SETUP-GUIDE.md").read_text(encoding="utf-8")
    assert "docs/TOOL-SETUP-GUIDE.md" in readme
    for required in (
        "OPENROUTER_API_KEY",
        "PR-Agent with OpenRouter",
        "Greptile",
        "Superpowers",
        "CodeQL",
        "Semgrep",
        "Gitleaks",
        "manifest is not execution",
        "exact pull-request revision",
    ):
        assert required in guide

