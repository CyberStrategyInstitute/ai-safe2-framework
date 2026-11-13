"""Collector behavior: signals, defaults, fail-closed paths, and the read boundary."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest
from assess_manifest_support import (
    HOME_ONLY_SENTINEL,
    agent_file,
    build_golden_project,
    write,
)

from safe2.manifest import collect as collect_module
from safe2.manifest.collect import ManifestCollectionError, collect_manifest, count_secret_findings
from safe2.manifest.heuristics import load_heuristics


def collect(project: Path, home: Path, **overrides):
    home.mkdir(parents=True, exist_ok=True)
    options: dict[str, Any] = {"project_name": "demo", "max_files": 10_000, "max_file_bytes": 5_000_000, "home": home}
    options.update(overrides)
    return collect_manifest(project, **options)


def agents_by_name(collection) -> dict[str, dict]:
    return {agent["name"]: agent for agent in collection.manifest["agents"]}


def test_agent_without_a_tools_list_inherits_the_settings_allow_list_names_only(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/general.md", agent_file("general", None))
    write(
        project,
        ".claude/settings.json",
        json.dumps({"permissions": {"allow": ["Bash(rm -rf SENTINEL_ARG:*)", "Read", "mcp__gmail__send_email"], "deny": ["Read"]}}),
    )
    collection = collect(project, tmp_path / "home")
    agent = agents_by_name(collection)["general"]
    assert agent["tools"] == ["Bash", "mcp__gmail__send_email"]  # specifier dropped; bare deny removed
    assert agent["sends_externally"] is True
    assert "SENTINEL_ARG" not in json.dumps(collection.manifest)
    signals = collection.notes["agent_signals"][0]
    assert signals["tools_inherited"] is True


def test_only_bare_ask_rules_count_as_approval_points(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/a.md", agent_file("a", "Read"))
    write(
        project,
        ".claude/settings.json",
        json.dumps({"permissions": {"ask": ["Bash(git push:*)", "Edit", "mcp__gmail__send_email"]}}),
    )
    agent = agents_by_name(collect(project, tmp_path / "home"))["a"]
    assert agent["approval_points"] == ["before_send", "before_write"]  # Bash(...) covers only a subset


def test_settings_level_bypass_mode_marks_claude_agents_unattended_but_not_other_harnesses(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/a.md", agent_file("a", "Read"))
    write(project, ".github/agents/review.agent.md", agent_file("review", "read"))
    write(project, ".claude/settings.json", json.dumps({"permissions": {"defaultMode": "bypassPermissions"}}))
    agents = agents_by_name(collect(project, tmp_path / "home"))
    assert agents["a"]["runs_unattended"] is True
    assert agents["review"]["harness"] == "github-copilot"
    assert agents["review"]["runs_unattended"] is False


def test_most_permissive_mode_across_settings_files_is_reported(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/settings.json", json.dumps({"permissions": {"defaultMode": "plan"}}))
    write(project, ".claude/settings.local.json", json.dumps({"permissions": {"defaultMode": "acceptEdits"}}))
    collection = collect(project, tmp_path / "home")
    assert collection.manifest["permissions"]["mode"] == "acceptEdits"


def test_state_files_and_headless_ci_markers_are_signals_not_silent_assumptions(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/a.md", agent_file("a", "Read"))
    write(project, "MEMORY.md", "# memory\n")
    write(project, "HEARTBEAT.md", "# heartbeat\n")
    write(project, ".github/workflows/agent.yml", "jobs:\n  x:\n    steps:\n      - run: claude -p 'do it'\n")
    collection = collect(project, tmp_path / "home")
    agent = agents_by_name(collection)["a"]
    assert agent["persistent_memory"] is True and agent["memory_provenance"] is False
    assert agent["runs_unattended"] is True
    signals = collection.notes["agent_signals"][0]
    assert "memory_state_file" in signals["memory_signals"]
    assert {"scheduled_asset", "ci_headless_marker"} <= set(signals["unattended_signals"])
    # Workflows are read for a marker only; they are not config files and no text is kept.
    assert all(not row["path"].startswith(".github/workflows") for row in collection.manifest["config_files"])


def test_colliding_names_are_disambiguated_by_path(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/reviewer.md", agent_file("reviewer", "Read"))
    write(project, "packages/x/.claude/agents/reviewer.md", agent_file("reviewer", "Read"))
    write(project, ".mcp.json", json.dumps({"mcpServers": {"s": {"command": "a"}}}))
    write(project, "packages/x/.mcp.json", json.dumps({"mcpServers": {"s": {"command": "b"}}}))
    collection = collect(project, tmp_path / "home")
    assert sorted(agent["name"] for agent in collection.manifest["agents"]) == [
        "reviewer [.claude/agents/reviewer.md]",
        "reviewer [packages/x/.claude/agents/reviewer.md]",
    ]
    assert sorted(server["name"] for server in collection.manifest["mcp_servers"]) == [
        "s [.mcp.json]",
        "s [packages/x/.mcp.json]",
    ]


def test_mcp_server_shapes_and_pinning_rules(tmp_path: Path) -> None:
    project = tmp_path / "p"
    digest = "cd" * 32
    write(
        project,
        ".mcp.json",
        json.dumps(
            {
                "mcpServers": {
                    "semver-only": {"command": "npx", "args": ["-y", "pkg@1.2.3"]},
                    "npm-digest": {"command": "npx", "args": [f"pkg@sha256:{digest}"]},
                    "events": {"url": "https://x.example/sse"},
                    "mtls": {"url": "https://x.example/mcp", "tls": {"cert": "c"}},
                    "oauth": {"url": "https://x.example/mcp", "oauth": {}},
                    "broken": {"disabled": True},
                }
            }
        ),
    )
    collection = collect(project, tmp_path / "home")
    servers = {server["name"]: server for server in collection.manifest["mcp_servers"]}
    assert servers["semver-only"]["pinned_digest"] is None  # a version is not a digest
    assert servers["npm-digest"]["pinned_digest"] == digest
    assert servers["events"]["transport"] == "sse"
    assert servers["mtls"]["auth_type"] == "mtls"
    assert servers["oauth"]["auth_type"] == "oauth"
    assert "broken" not in servers
    assert any(row["path"].endswith("#broken") for row in collection.notes["not_collected"])


def test_config_digest_is_redacted_and_stable_across_env_value_changes(tmp_path: Path) -> None:
    def digest_for(value: str, key: str = "API_TOKEN") -> str:
        project = tmp_path / f"p-{value}-{key}"
        write(project, ".mcp.json", json.dumps({"mcpServers": {"s": {"command": "npx", "env": {key: value}}}}))
        return collect(project, tmp_path / "home").manifest["mcp_servers"][0]["config_digest"]

    assert digest_for("one-value-aaaa") == digest_for("two-value-bbbb")
    assert digest_for("one-value-aaaa") != digest_for("one-value-aaaa", key="OTHER_TOKEN")


def test_secret_counting_detects_known_formats_assignments_and_keys_but_not_placeholders() -> None:
    heuristics = load_heuristics()
    fake = "sk-" + "ant-" + "A" * 40
    text = "\n".join(
        [
            f"ANTHROPIC_API_KEY={fake}",
            "DB_PASSWORD=hunter2hunter2",
            "STRIPE_SECRET=${STRIPE_SECRET}",
            "API_KEY=<your key here>",
            "API_TOKEN=changeme-please",
            "-----BEGIN " + "PRIVATE KEY-----",
            "PORT=8080",
        ]
    )
    assert count_secret_findings(text, markdown=False, heuristics=heuristics) == 3
    prose = "The password: must contain at least eight characters\n" + fake
    assert count_secret_findings(prose, markdown=True, heuristics=heuristics) == 1


def test_truncated_inventory_fails_closed(tmp_path: Path) -> None:
    project = tmp_path / "p"
    for index in range(8):
        write(project, f"src/f{index}.py", "x = 1\n")
    write(project, ".mcp.json", json.dumps({"mcpServers": {"s": {"command": "npx"}}}))
    with pytest.raises(ManifestCollectionError, match="limits.max_files"):
        collect(project, tmp_path / "home", max_files=3)


def test_unparseable_or_oversized_project_config_fails_closed(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".mcp.json", "{not json")
    with pytest.raises(ManifestCollectionError, match=r"\.mcp\.json: not a valid JSON object"):
        collect(project, tmp_path / "home")
    big = tmp_path / "q"
    write(big, ".claude/settings.json", "{" + " " * 2000 + "}")
    with pytest.raises(ManifestCollectionError, match="size_limit"):
        collect(big, tmp_path / "home", max_file_bytes=1000)


def test_symlinked_project_config_is_not_followed(tmp_path: Path) -> None:
    project = tmp_path / "p"
    outside = tmp_path / "outside.json"
    outside.write_text(json.dumps({"mcpServers": {"leak": {"command": "x"}}}), encoding="utf-8")
    project.mkdir()
    (project / ".mcp.json").symlink_to(outside)
    collection = collect(project, tmp_path / "home")
    assert collection.manifest["mcp_servers"] == []  # inventory skips symlinks; nothing outside is read


def test_user_level_reads_stay_inside_doctors_known_locations(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "p"
    build_golden_project(project)
    home = tmp_path / "home"
    write(home, ".claude/settings.json", json.dumps({"permissions": {"defaultMode": "bypassPermissions"}}))
    write(home, ".claude/agents/personal.md", agent_file("personal", "Read"))
    write(home, ".codex/config.toml", '[mcp_servers.codex_tool]\ncommand = "npx"\n')
    write(home, ".claude.json", json.dumps({"oauth": HOME_ONLY_SENTINEL}))
    write(home, ".ssh/id_ed25519", HOME_ONLY_SENTINEL)
    write(home, ".aws/credentials", HOME_ONLY_SENTINEL)
    read: list[Path] = []
    real = collect_module.read_regular_bounded

    def spy(path: Path, *, limit: int) -> bytes:
        read.append(Path(path).resolve())
        return real(path, limit=limit)

    monkeypatch.setattr(collect_module, "read_regular_bounded", spy)
    collection = collect(project, home)
    inside_project = project.resolve()
    allowed_home = {(home / ".claude").resolve(), (home / ".codex").resolve()}
    for path in read:
        assert path.is_relative_to(inside_project) or any(path.is_relative_to(base) for base in allowed_home), path
    assert not any(path.name in {".claude.json", "id_ed25519", "credentials"} for path in read)
    assert HOME_ONLY_SENTINEL not in json.dumps(collection.manifest)
    paths = {row["path"] for row in collection.manifest["config_files"]}
    assert {"~/.claude/settings.json", "~/.claude/agents/personal.md", "~/.codex/config.toml"} <= paths
    assert "codex_tool" in {server["name"] for server in collection.manifest["mcp_servers"]}
    assert agents_by_name(collection)["personal"]["runs_unattended"] is True  # user-level bypass applies


def test_unreadable_user_level_config_fails_closed_instead_of_looking_safe(tmp_path: Path) -> None:
    # A dotfiles-managed ~/.claude that sets bypassPermissions must not be silently dropped.
    project = tmp_path / "p"
    project.mkdir()
    real_dotfiles = tmp_path / "dotfiles"
    write(real_dotfiles, "settings.json", json.dumps({"permissions": {"defaultMode": "bypassPermissions"}}))
    home = tmp_path / "home"
    home.mkdir()
    (home / ".claude").symlink_to(real_dotfiles)
    with pytest.raises(ManifestCollectionError, match=r"~/\.claude/settings\.json: unreadable \(symlink\)"):
        collect(project, home)


def test_unparseable_user_level_config_fails_closed(tmp_path: Path) -> None:
    project = tmp_path / "p"
    project.mkdir()
    home = tmp_path / "home"
    write(home, ".claude/settings.json", "{not json")
    with pytest.raises(ManifestCollectionError, match=r"~/\.claude/settings\.json: not a valid JSON object"):
        collect(project, home)


def test_secret_regex_is_not_catastrophic_on_hostile_lines() -> None:
    heuristics = load_heuristics()
    hostile = ["secret" * 1666, "a" * 10_000, "token=" + "a" * 200_000, ("secret " * 2000), "authorization: " + " " * 50_000]
    started = time.monotonic()
    for line in hostile:
        count_secret_findings(line + "\n", markdown=False, heuristics=heuristics)
    assert time.monotonic() - started < 5.0


def test_a_secret_past_ten_thousand_characters_on_one_line_is_still_counted() -> None:
    heuristics = load_heuristics()
    minified = '{"a":"' + "x" * 20_000 + '","password":"hunter2hunter2"}'
    assert count_secret_findings(minified, markdown=False, heuristics=heuristics) == 1


def test_agent_without_tools_inherits_every_configured_mcp_server(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/general.md", agent_file("general", None))
    write(project, ".mcp.json", json.dumps({"mcpServers": {"gmail": {"command": "x"}, "stripe": {"command": "y"}}}))
    agent = agents_by_name(collect(project, tmp_path / "home"))["general"]
    assert agent["tools"] == ["mcp__gmail", "mcp__stripe"]
    assert agent["sends_externally"] is True and agent["moves_money"] is True
    assert agent["budget_ceiling_configured"] is False


def test_an_explicit_empty_tools_list_inherits_nothing(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/locked.md", "---\nname: locked\ntools: []\n---\nbody\n")
    write(project, ".claude/settings.json", json.dumps({"permissions": {"allow": ["Task"]}}))
    write(project, ".mcp.json", json.dumps({"mcpServers": {"gmail": {"command": "x"}, "stripe": {"command": "y"}}}))
    collection = collect(project, tmp_path / "home")
    agent = agents_by_name(collection)["locked"]
    assert agent["tools"] == []
    assert not agent["sends_externally"] and not agent["moves_money"] and not agent["can_spawn_subagents"]
    signals = {entry["subject"]: entry for entry in collection.notes["agent_signals"]}
    assert signals["agent:.claude/agents/locked.md"]["tools_inherited"] is False


def test_comma_inside_a_tool_specifier_never_leaks_a_fragment(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/a.md", agent_file("a", "Bash(a,SECRETISH_b,c), Read"))
    assert agents_by_name(collect(project, tmp_path / "home"))["a"]["tools"] == ["Bash", "Read"]


def test_unknown_permission_mode_and_hook_event_text_is_not_forwarded(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(
        project,
        ".claude/settings.json",
        json.dumps(
            {
                "permissions": {"defaultMode": "SENTINEL arbitrary text"},
                "hooks": {"Weird Event !! SENTINEL": [{"hooks": [{"type": "command", "command": "x"}]}]},
            }
        ),
    )
    manifest = collect(project, tmp_path / "home").manifest
    assert manifest["permissions"]["mode"] == "other"
    assert manifest["hooks"][0]["event"] == "other"
    assert "SENTINEL" not in json.dumps(manifest)


def test_too_many_hooks_or_tools_fail_closed_rather_than_truncate(tmp_path: Path) -> None:
    project = tmp_path / "p"
    hooks = {"PreToolUse": [{"hooks": [{"type": "command", "command": f"c{index}"} for index in range(201)]}]}
    write(project, ".claude/settings.json", json.dumps({"hooks": hooks}))
    with pytest.raises(ManifestCollectionError, match="distinct hooks"):
        collect(project, tmp_path / "home")
    many = tmp_path / "q"
    write(many, ".claude/agents/a.md", agent_file("a", ", ".join(f"tool{index}" for index in range(501))))
    with pytest.raises(ManifestCollectionError, match="more than 500 tools"):
        collect(many, tmp_path / "home")


def long_frontmatter_agent(padding_lines: int, *, closed: bool = True) -> str:
    padding = "".join(f"  continuation line {index}\n" for index in range(padding_lines))
    closing = "---\n" if closed else ""
    return f"---\nname: long\ndescription: |\n{padding}tools: Task\npermissionMode: bypassPermissions\n{closing}body\n"


def test_frontmatter_past_the_line_limit_fails_closed_instead_of_dropping_fields(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/long.md", long_frontmatter_agent(250))
    with pytest.raises(ManifestCollectionError, match=r"\.claude/agents/long\.md.*closing"):
        collect(project, tmp_path / "home")


def test_frontmatter_that_never_closes_fails_closed(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/open.md", long_frontmatter_agent(3, closed=False))
    with pytest.raises(ManifestCollectionError, match=r"\.claude/agents/open\.md.*closing"):
        collect(project, tmp_path / "home")


def test_long_but_closed_frontmatter_within_the_limit_keeps_every_field(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/long.md", long_frontmatter_agent(150))
    agent = agents_by_name(collect(project, tmp_path / "home"))["long"]
    assert agent["can_spawn_subagents"] is True and agent["runs_unattended"] is True


def test_a_markdown_agent_without_frontmatter_is_still_accepted(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/plain.md", "# Plain agent\n\nNo frontmatter here.\n")
    assert agents_by_name(collect(project, tmp_path / "home"))["plain"]["tools"] == []


def test_a_nested_project_deny_does_not_remove_tools_from_a_root_agent(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/root.md", agent_file("root", "Task, Read"))
    write(project, "packages/x/.claude/settings.json", json.dumps({"permissions": {"deny": ["Task"]}}))
    agent = agents_by_name(collect(project, tmp_path / "home"))["root"]
    assert agent["tools"] == ["Read", "Task"] and agent["can_spawn_subagents"] is True


def test_a_nested_project_ask_adds_no_approval_points_to_a_root_agent(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/root.md", agent_file("root", "Read"))
    write(project, "packages/x/.claude/settings.json", json.dumps({"permissions": {"ask": ["Edit"]}}))
    assert agents_by_name(collect(project, tmp_path / "home"))["root"]["approval_points"] == []


def test_a_nested_agent_is_still_restricted_by_its_own_nested_settings(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/root.md", agent_file("root", "Task, Read"))
    write(project, "packages/x/.claude/agents/child.md", agent_file("child", "Task, Read"))
    write(
        project,
        "packages/x/.claude/settings.json",
        json.dumps({"permissions": {"deny": ["Task"], "ask": ["Edit"]}}),
    )
    agents = agents_by_name(collect(project, tmp_path / "home"))
    assert agents["child"]["tools"] == ["Read"] and agents["child"]["can_spawn_subagents"] is False
    assert agents["child"]["approval_points"] == ["before_write"]
    assert agents["root"]["can_spawn_subagents"] is True and agents["root"]["approval_points"] == []


def test_user_level_deny_and_ask_rules_still_apply_to_every_claude_agent(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/root.md", agent_file("root", "Task, Read"))
    write(project, "packages/x/.claude/agents/child.md", agent_file("child", "Task, Read"))
    home = tmp_path / "home"
    write(home, ".claude/settings.json", json.dumps({"permissions": {"deny": ["Task"], "ask": ["Edit"]}}))
    agents = agents_by_name(collect(project, home))
    for name in ("root", "child"):
        assert agents[name]["tools"] == ["Read"] and agents[name]["approval_points"] == ["before_write"]


def test_the_settings_scoping_rule_is_recorded_in_the_local_notes(tmp_path: Path) -> None:
    project = tmp_path / "p"
    project.mkdir()
    limitations = " ".join(collect(project, tmp_path / "home").notes["limitations"])
    assert "deny and ask rules apply only" in limitations


def test_lone_surrogates_in_config_text_do_not_crash_hashing(tmp_path: Path) -> None:
    project = tmp_path / "p"
    (project / ".claude").mkdir(parents=True)
    (project / ".claude" / "settings.json").write_text(
        '{"hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "\\ud800"}]}]}}', encoding="utf-8"
    )
    assert len(collect(project, tmp_path / "home").manifest["hooks"]) == 1


def test_empty_project_produces_a_valid_empty_manifest(tmp_path: Path) -> None:
    project = tmp_path / "p"
    project.mkdir()
    collection = collect(project, tmp_path / "home")
    assert collection.manifest["agents"] == [] and collection.manifest["mcp_servers"] == []
    assert collection.manifest["project"] == {"name": "demo"}
