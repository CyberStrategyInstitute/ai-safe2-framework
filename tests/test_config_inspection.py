from __future__ import annotations

import json
from pathlib import Path

from safe2.discovery.assets import inventory_assets
from safe2.discovery.config import inspect_config, inspect_inventory


def test_mcp_inspection_emits_structure_not_secrets(tmp_path: Path):
    path = tmp_path / ".mcp.json"
    path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "remote-research": {
                        "url": "https://secret.internal/mcp",
                        "headers": {"Authorization": "Bearer VERY_SECRET"},
                    },
                    "local-files": {
                        "command": "/secret/path/server",
                        "args": ["--token", "VERY_SECRET"],
                        "env": {"API_TOKEN": "VERY_SECRET"},
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    result = inspect_config(path)
    serialized = json.dumps(result)
    assert result["status"] == "completed"
    assert [row["transport"] for row in result["mcp_servers"]] == ["local", "remote"]
    assert result["mcp_servers"][0]["environment_key_count"] == 1
    assert "VERY_SECRET" not in serialized
    assert "secret.internal" not in serialized
    assert "/secret/path" not in serialized


def test_harness_inspection_summarizes_permissions_hooks_and_policy(tmp_path: Path):
    folder = tmp_path / ".claude"
    folder.mkdir()
    path = folder / "settings.json"
    path.write_text(
        json.dumps(
            {
                "permissions": {"allow": ["Read", "Bash(test *)"], "deny": ["Bash(rm *)"]},
                "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": ["secret command"]}]},
                "permission_mode": "default",
            }
        ),
        encoding="utf-8",
    )
    result = inspect_config(path)
    assert result["permission_rule_counts"] == {"allow": 2, "deny": 1}
    assert result["hook_events"] == [{"event": "PreToolUse", "registration_count": 1}]
    assert result["runtime_policy"] == {"approval_policy": "default"}
    assert "secret command" not in json.dumps(result)


def test_inventory_inspects_only_recognized_config_assets(tmp_path: Path):
    config = tmp_path / ".mcp.json"
    config.write_text('{"mcpServers": {}}', encoding="utf-8")
    (tmp_path / "ordinary.json").write_text('{"token": "secret"}', encoding="utf-8")
    inventory = inventory_assets(tmp_path)
    result = inspect_inventory(tmp_path, inventory)
    assert result["summary"]["candidates"] == 1
    assert result["summary"]["completed"] == 1
    assert result["privacy"]["secret_values_emitted"] is False


def test_oversized_and_invalid_configs_are_explicitly_incomplete(tmp_path: Path):
    oversized = tmp_path / ".mcp.json"
    oversized.write_text("x" * 20, encoding="utf-8")
    assert inspect_config(oversized, max_bytes=10)["reason"] == "size_limit"
    invalid = tmp_path / "settings.json"
    invalid.write_text("not json", encoding="utf-8")
    result = inspect_config(invalid)
    assert result["status"] == "failed"
    assert result["error_type"] == "JSONDecodeError"


def test_inventory_rejects_paths_outside_assessed_root(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text('{"secret": "DO_NOT_READ"}', encoding="utf-8")
    inventory = {
        "assets": [
            {"type": "mcp_configuration", "path": "../outside.json"},
            {"type": "mcp_configuration", "path": str(outside.resolve())},
        ]
    }
    result = inspect_inventory(root, inventory)
    assert result["summary"]["completed"] == 0
    assert result["summary"]["incomplete"] == 2
    assert all(row["reason"] == "outside_root" for row in result["files"])
    assert "DO_NOT_READ" not in json.dumps(result)
