from __future__ import annotations

import json
from pathlib import Path

import pytest

from safe2.discovery.drift import load_baseline
from safe2.discovery.integrity import seal_inventory, verify_inventory


def _inventory() -> dict[str, object]:
    return {
        "schema_version": "safe2.discovery.v1",
        "collected_at": "2026-09-04T00:00:00+00:00",
        "scope": {"type": "local", "root": "/repo"},
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


def test_sealed_inventory_verifies_and_is_deterministic():
    first = seal_inventory(_inventory())
    second = seal_inventory(_inventory())
    assert verify_inventory(first) == "valid"
    assert first["integrity"] == second["integrity"]
    assert first["integrity"]["authenticity"] == "unsigned"


def test_mutated_sealed_inventory_is_rejected(tmp_path: Path):
    inventory = seal_inventory(_inventory())
    inventory["harnesses"] = [{"id": "unexpected"}]
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(inventory), encoding="utf-8")
    assert verify_inventory(inventory) == "invalid"
    with pytest.raises(ValueError, match="integrity verification failed"):
        load_baseline(path)


def test_unsigned_legacy_inventory_remains_compatible(tmp_path: Path):
    inventory = _inventory()
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(inventory), encoding="utf-8")
    assert load_baseline(path) == inventory
    assert verify_inventory(inventory) == "not_present"
