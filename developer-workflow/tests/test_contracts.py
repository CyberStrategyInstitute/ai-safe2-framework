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

