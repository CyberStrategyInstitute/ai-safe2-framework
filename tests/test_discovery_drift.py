from __future__ import annotations

import json
from pathlib import Path

import pytest

from safe2.discovery.drift import compare_discovery, load_baseline


def _inventory(*, harnesses=None, assets=None, configs=None, targets=None):
    return {
        "schema_version": "safe2.discovery.v1",
        "collected_at": "2026-09-04T00:00:00+00:00",
        "scope": {"type": "local", "root": "/repo"},
        "harnesses": harnesses or [],
        "targets": targets or [],
        "asset_inventory": {"assets": assets or []},
        "configuration_inspection": {"files": configs or []},
    }


def test_drift_detects_harness_asset_config_and_lost_target():
    baseline = _inventory(
        harnesses=[{"id": "codex"}],
        assets=[{"type": "agent_instruction", "path": "AGENTS.md"}],
        configs=[{"path": ".mcp.json", "status": "completed", "content_sha256": "old"}],
        targets=[{"id": "ssh:audit@host:22", "status": "completed"}],
    )
    current = _inventory(
        harnesses=[{"id": "codex"}, {"id": "claude-code"}],
        assets=[
            {"type": "agent_instruction", "path": "AGENTS.md"},
            {"type": "agent_skill", "path": ".agents/skills/new/SKILL.md"},
        ],
        configs=[{"path": ".mcp.json", "status": "completed", "content_sha256": "new"}],
        targets=[],
    )
    result = compare_discovery(current, baseline)
    categories = {row["category"] for row in result["findings"]}
    assert result["changes"] == 4
    assert categories == {"harness_drift", "asset_drift", "configuration_drift", "coverage_drift"}
    assert any(row["severity"] == "high" for row in result["findings"])


def test_removed_assets_are_not_silently_ignored():
    baseline = _inventory(assets=[{"type": "agent_instruction", "path": "CLAUDE.md"}])
    result = compare_discovery(_inventory(), baseline)
    assert result["changes"] == 1
    assert result["findings"][0]["severity"] == "low"
    assert "removed" in result["findings"][0]["title"].lower()


@pytest.mark.parametrize(
    ("baseline_asset", "current_asset", "basis"),
    [
        (
            {
                "type": "agent_instruction",
                "path": "AGENTS.md",
                "size_bytes": 10,
                "modified_at": "2026-09-01T00:00:00Z",
            },
            {
                "type": "agent_instruction",
                "path": "AGENTS.md",
                "size_bytes": 11,
                "modified_at": "2026-09-02T00:00:00Z",
            },
            "size or modification time",
        ),
        (
            {
                "type": "agent_skill",
                "path": "skill/SKILL.md",
                "content_sha256": "a" * 64,
            },
            {
                "type": "agent_skill",
                "path": "skill/SKILL.md",
                "content_sha256": "b" * 64,
            },
            "content hash",
        ),
    ],
)
def test_existing_asset_modifications_are_detected(baseline_asset, current_asset, basis):
    result = compare_discovery(
        _inventory(assets=[current_asset]), _inventory(assets=[baseline_asset])
    )
    assert result["changes"] == 1
    assert result["findings"][0]["category"] == "asset_drift"
    assert "changed" in result["findings"][0]["title"].lower()
    assert basis in result["findings"][0]["facts"][0]


def test_baseline_loader_rejects_wrong_schema_and_symlink(tmp_path: Path):
    path = tmp_path / "wrong.json"
    path.write_text(json.dumps({"schema_version": "unknown"}), encoding="utf-8")
    with pytest.raises(ValueError, match="not a safe2.discovery.v1"):
        load_baseline(path)
    link = tmp_path / "link.json"
    try:
        link.symlink_to(path)
    except OSError:
        return
    with pytest.raises(ValueError, match="symbolic link"):
        load_baseline(link)


def test_scope_change_is_disclosed():
    baseline = _inventory()
    current = _inventory()
    current["scope"] = {"type": "local", "root": "/different"}
    result = compare_discovery(current, baseline)
    assert result["scope_changed"] is True
    assert result["changes"] == 1
    assert result["findings"][0]["id"] == "DRIFT-SCOPE-CHANGED"
    assert result["findings"][0]["severity"] == "high"
