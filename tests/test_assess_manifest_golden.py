"""Golden fixture: planted facts appear as exact flags and no sensitive text leaves the machine."""

from __future__ import annotations

import json
import re
import stat
from pathlib import Path

import pytest
from assess_manifest_support import (
    FAKE_PROVIDER_KEY,
    LEAK_SENTINELS,
    PINNED_HEX,
    build_golden_project,
    bundle_text,
    init_project,
    isolate_home,
)
from click.testing import CliRunner

from safe2.cli import cli

MANIFEST_ARGS = ["--manifest", "--scan-content", "--inspect-config", "--no-wsl"]


@pytest.fixture
def golden(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    isolate_home(monkeypatch, tmp_path / "home")
    project = tmp_path / "project"
    build_golden_project(project)
    init_project(project)
    bundle = tmp_path / "bundle"
    result = CliRunner().invoke(cli, ["assess", str(project), *MANIFEST_ARGS, "--output-dir", str(bundle)])
    assert result.exit_code == 0, result.output
    manifest = json.loads((bundle / "aisafe2-project-manifest-1.json").read_text(encoding="utf-8"))
    return {"project": project, "bundle": bundle, "manifest": manifest, "output": result.output}


def _agents(manifest: dict) -> dict[str, dict]:
    return {agent["name"]: agent for agent in manifest["agents"]}


def test_planted_agent_flags_are_exactly_the_planted_facts(golden) -> None:
    agents = _agents(golden["manifest"])
    assert set(agents) == {"orchestrator", "mailer", "notekeeper", "reader", "generalist"}
    flags = ("can_spawn_subagents", "persistent_memory", "runs_unattended", "sends_externally", "moves_money")
    planted = {
        "orchestrator": {"can_spawn_subagents"},
        "mailer": {"runs_unattended", "sends_externally"},
        "notekeeper": {"persistent_memory"},
        "reader": set(),
        "generalist": set(),
    }
    for name, expected in planted.items():
        actual = {flag for flag in flags if agents[name][flag]}
        assert actual == expected, (name, actual)
    # Facts the CLI cannot detect are written unfavourably, and only where they are required.
    assert agents["orchestrator"]["mandate_configured"] is False
    assert agents["notekeeper"]["memory_provenance"] is False
    for name in ("mailer", "reader"):
        assert "mandate_configured" not in agents[name]
        assert "memory_provenance" not in agents[name]
        assert "budget_ceiling_configured" not in agents[name]
    assert "budget_ceiling_configured" not in agents["orchestrator"]


def test_tool_names_carry_no_arguments_and_agents_have_definition_digests(golden) -> None:
    agents = _agents(golden["manifest"])
    assert agents["mailer"]["tools"] == ["Read", "mcp__gmail__send_email"]
    assert agents["orchestrator"]["tools"] == ["Grep", "Read", "Task"]
    # Inherited: the settings allow-list (names only, specifier dropped) plus each configured MCP server.
    assert agents["generalist"]["tools"] == [
        "Bash", "Read", "mcp__filesystem", "mcp__pinned-tool", "mcp__remote-docs",
    ]
    for agent in agents.values():
        assert re.fullmatch(r"[0-9a-f]{64}", agent["definition_digest"])
        assert agent["harness"] == "claude-code"


def test_unpinned_server_has_null_digest_and_pinned_server_carries_only_the_hex_digest(golden) -> None:
    servers = {server["name"]: server for server in golden["manifest"]["mcp_servers"]}
    assert servers["filesystem"]["pinned_digest"] is None
    assert servers["filesystem"]["transport"] == "stdio"
    assert servers["filesystem"]["auth_type"] == "api_key"
    assert servers["pinned-tool"]["pinned_digest"] == PINNED_HEX
    assert servers["remote-docs"]["transport"] == "streamable-http"
    assert servers["remote-docs"]["auth_type"] == "bearer"
    assert servers["remote-docs"]["pinned_digest"] is None
    for server in servers.values():
        assert re.fullmatch(r"[0-9a-f]{64}", server["config_digest"])
        assert set(server) == {"name", "transport", "pinned_digest", "auth_type", "config_digest"}


def test_env_file_reports_a_secret_count_and_never_the_value(golden) -> None:
    files = {row["path"]: row for row in golden["manifest"]["config_files"]}
    assert files[".env"]["secret_findings"] > 0
    assert re.fullmatch(r"[0-9a-f]{64}", files[".env"]["sha256"])
    # Hard-coded env and header values in the MCP config are secret findings too.
    assert files[".mcp.json"]["secret_findings"] == 2
    assert files[".claude/settings.json"]["secret_findings"] == 0
    assert files[".claude/agents/reader.md"]["secret_findings"] == 0
    assert set(files) == {
        ".env", ".mcp.json", ".claude/settings.json",
        ".claude/agents/orchestrator.md", ".claude/agents/mailer.md",
        ".claude/agents/notekeeper.md", ".claude/agents/reader.md", ".claude/agents/generalist.md",
    }


def test_permissions_and_hooks_are_counts_and_digests_only(golden) -> None:
    manifest = golden["manifest"]
    assert manifest["permissions"]["mode"] == "default"
    assert manifest["permissions"]["allow_rules"] == 2
    assert manifest["permissions"]["deny_rules"] == 1
    assert re.fullmatch(r"[0-9a-f]{64}", manifest["permissions"]["digest"])
    assert [hook["event"] for hook in manifest["hooks"]] == ["PreToolUse"]
    assert re.fullmatch(r"[0-9a-f]{64}", manifest["hooks"][0]["command_digest"])
    assert set(manifest["hooks"][0]) == {"event", "command_digest"}
    assert agents_approval(manifest) == ["before_write"]


def agents_approval(manifest: dict) -> list[str]:
    return _agents(manifest)["reader"]["approval_points"]


def test_unknowable_keys_are_omitted_and_explained_only_in_the_local_bundle(golden) -> None:
    manifest = golden["manifest"]
    assert "ci_gate" not in manifest
    assert "project_id" not in manifest["project"]
    assert manifest["project"] == {"name": "golden"}
    notes = json.loads((golden["bundle"] / "manifest-collection-notes.json").read_text(encoding="utf-8"))
    assert {row["key"] for row in notes["omitted_keys"]} == {"ci_gate", "project.project_id"}
    reasons = {(row["subject"], row["flag"]) for row in notes["flag_reasons"]}
    assert ("agent:.claude/agents/orchestrator.md", "mandate_configured") in reasons
    assert ("agent:.claude/agents/notekeeper.md", "memory_provenance") in reasons
    assert any(row["path"] == "~/.claude.json" for row in notes["not_collected"])
    # None of the explanation is in the manifest that may be sent.
    assert "cannot_detect" not in json.dumps(manifest) and "reason" not in json.dumps(manifest)


def test_no_secret_prompt_argument_command_or_env_value_appears_anywhere(golden) -> None:
    everything = bundle_text(golden["bundle"]) + golden["output"]
    for sentinel in LEAK_SENTINELS:
        assert sentinel not in everything, sentinel
    assert FAKE_PROVIDER_KEY not in everything


def test_manifest_file_is_private_and_deterministically_formatted(golden) -> None:
    path = golden["bundle"] / "aisafe2-project-manifest-1.json"
    assert stat.S_IMODE(path.stat().st_mode) & 0o077 == 0
    raw = path.read_text(encoding="utf-8")
    assert raw.endswith("\n")
    parsed = json.loads(raw)
    assert raw == json.dumps(parsed, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", parsed["generated_at"])


def test_same_tree_gives_identical_manifest_bytes_except_generated_at(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    isolate_home(monkeypatch, tmp_path / "home")
    project = tmp_path / "project"
    build_golden_project(project)
    init_project(project)
    runner = CliRunner()
    first, second = tmp_path / "one", tmp_path / "two"
    for bundle in (first, second):
        result = runner.invoke(cli, ["assess", str(project), *MANIFEST_ARGS, "--output-dir", str(bundle)])
        assert result.exit_code == 0, result.output

    def normalized(bundle: Path) -> str:
        text = (bundle / "aisafe2-project-manifest-1.json").read_text(encoding="utf-8")
        return re.sub(r'"generated_at": "[^"]+"', '"generated_at": "T"', text)

    assert normalized(first) == normalized(second)
    notes = [json.loads((b / "manifest-collection-notes.json").read_text(encoding="utf-8")) for b in (first, second)]
    for body in notes:
        body.pop("manifest_sha256")  # digests the bytes, which include generated_at
    assert notes[0] == notes[1]
