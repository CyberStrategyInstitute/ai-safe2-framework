from __future__ import annotations

from pathlib import Path

from safe2.discovery.assets import inventory_assets
from safe2.discovery.posture import assess_posture


def test_asset_inventory_classifies_without_reading_contents(tmp_path: Path):
    files = {
        "AGENTS.md": "SECRET_INSTRUCTION",
        ".mcp.json": "SECRET_TOKEN",
        ".github/workflows/agent.yml": "SECRET_CI_VALUE",
        ".agents/skills/review/SKILL.md": "SECRET_SKILL",
        "MEMORY.md": "SECRET_MEMORY",
        "infra/main.tf": "SECRET_CLOUD_VALUE",
        "Dockerfile": "SECRET_CONTAINER_VALUE",
    }
    for relative, content in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    result = inventory_assets(tmp_path)
    assert result["privacy"]["file_contents_collected"] is False
    assert result["counts"] == {
        "mcp_configuration": 1,
        "agent_instruction": 1,
        "container_definition": 1,
        "persistent_agent_state": 1,
        "ci_pipeline": 1,
        "agent_skill": 1,
        "infrastructure_as_code": 1,
    }
    serialized = str(result)
    assert "SECRET_" not in serialized


def test_asset_inventory_skips_dependencies_and_symlinks(tmp_path: Path):
    dependency = tmp_path / "node_modules/pkg/SKILL.md"
    dependency.parent.mkdir(parents=True)
    dependency.write_text("ignored", encoding="utf-8")
    target = tmp_path / "AGENTS.md"
    target.write_text("policy", encoding="utf-8")
    link = tmp_path / "linked-SKILL.md"
    try:
        link.symlink_to(target)
    except OSError:
        pass
    result = inventory_assets(tmp_path)
    assert result["counts"] == {"agent_instruction": 1}


def test_opt_in_asset_hashing_emits_digests_not_contents(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text("SECRET_POLICY", encoding="utf-8")
    result = inventory_assets(tmp_path, hash_contents=True)
    asset = result["assets"][0]
    assert len(asset["content_sha256"]) == 64
    assert asset["hash_status"] == "completed"
    assert result["privacy"]["file_contents_read_locally"] is True
    assert result["privacy"]["file_contents_emitted"] is False
    assert "SECRET_POLICY" not in str(result)


def test_asset_hashing_is_bounded(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text("large policy", encoding="utf-8")
    result = inventory_assets(tmp_path, hash_contents=True, max_hash_bytes=1)
    assert result["assets"][0]["content_sha256"] is None
    assert result["assets"][0]["hash_status"] == "size_limit"


def test_asset_inventory_skips_generated_test_directories(tmp_path: Path):
    generated = tmp_path / ".test-temp-42/case/.mcp.json"
    generated.parent.mkdir(parents=True)
    generated.write_text('{"mcpServers": {"false-positive": {}}}', encoding="utf-8")
    result = inventory_assets(tmp_path)
    assert result["assets"] == []


def test_asset_truncation_becomes_high_coverage_gap(tmp_path: Path):
    for number in range(3):
        (tmp_path / f"file-{number}.txt").write_text("x", encoding="utf-8")
    assets = inventory_assets(tmp_path, max_files=1)
    posture = assess_posture(
        {
            "scope": {"root": str(tmp_path)},
            "harnesses": [],
            "targets": [],
            "asset_inventory": assets,
        }
    )
    assert assets["truncated"] is True
    finding = next(row for row in posture["findings"] if row["id"] == "ASSET-INVENTORY-TRUNCATED")
    assert finding["severity"] == "high"


def test_sensitive_asset_presence_creates_review_not_failure(tmp_path: Path):
    (tmp_path / "MEMORY.md").write_text("state", encoding="utf-8")
    (tmp_path / "HEARTBEAT.md").write_text("schedule", encoding="utf-8")
    skill = tmp_path / ".agents/skills/demo/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("skill", encoding="utf-8")
    assets = inventory_assets(tmp_path)
    posture = assess_posture(
        {"scope": {"root": str(tmp_path)}, "harnesses": [], "targets": [], "asset_inventory": assets}
    )
    assert posture["disposition"] == "REVIEW"
    assert any(row["id"] == "PERSISTENT-STATE-REVIEW" for row in posture["findings"])
    assert any(row["id"] == "SCHEDULED-AUTONOMY-REVIEW" for row in posture["findings"])
    assert any(row["id"] == "SKILL-SUPPLY-CHAIN-REVIEW" for row in posture["findings"])
