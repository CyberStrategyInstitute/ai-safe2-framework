from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = ROOT / "scripts" / "validate_workflow.py"
    spec = importlib.util.spec_from_file_location("validate_workflow", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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

