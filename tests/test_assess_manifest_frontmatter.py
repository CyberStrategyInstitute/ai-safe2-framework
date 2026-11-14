"""Agent frontmatter parsing: YAML comments and unsupported constructs never yield favourable flags.

The parser reads only five allowlisted keys by hand (no YAML dependency). Whatever it cannot read
unambiguously must fail collection; silently dropping a tool or a permission mode would report
`can_spawn_subagents` or `runs_unattended` as false for an agent that has them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from assess_manifest_support import write

from safe2.manifest.collect import ManifestCollectionError, _parse_frontmatter, collect_manifest


def collect(project: Path, home: Path):
    home.mkdir(parents=True, exist_ok=True)
    return collect_manifest(project, project_name="demo", max_files=10_000, max_file_bytes=5_000_000, home=home)


def agent(tmp_path: Path, frontmatter: str, *, name: str = "worker") -> dict[str, Any]:
    project = tmp_path / "p"
    write(project, f".claude/agents/{name}.md", f"---\n{frontmatter}---\nbody\n")
    agents = {item["name"]: item for item in collect(project, tmp_path / "home").manifest["agents"]}
    return agents[name]


def rejected(tmp_path: Path, frontmatter: str) -> str:
    project = tmp_path / "p"
    write(project, ".claude/agents/bad.md", f"---\nname: bad\n{frontmatter}---\nbody\n")
    with pytest.raises(ManifestCollectionError, match=r"\.claude/agents/bad\.md") as caught:
        collect(project, tmp_path / "home")
    return str(caught.value)


# --- inline comments (Codex review M1) -------------------------------------------------------


@pytest.mark.parametrize(
    "tools_text",
    [
        "tools: [Read, Task] # delegation\n",
        "tools: [Read, Task]  #delegation\n",
        "tools: Read, Task # delegation\n",
        "tools: 'Read, Task' # delegation\n",
        "tools: # delegation\n  - Read # reads\n  - Task # delegation\n",
        'tools: ["Read", "Task"] # delegation\n',
    ],
)
def test_an_inline_comment_on_tools_does_not_hide_the_task_tool(tmp_path: Path, tools_text: str) -> None:
    result = agent(tmp_path, tools_text)
    assert result["tools"] == ["Read", "Task"]
    assert result["can_spawn_subagents"] is True
    assert result["mandate_configured"] is False


def test_an_inline_comment_on_disallowed_tools_still_removes_the_tool(tmp_path: Path) -> None:
    result = agent(tmp_path, "tools: [Read, Task]\ndisallowedTools: [Task] # no delegation here\n")
    assert result["tools"] == ["Read"] and result["can_spawn_subagents"] is False
    block = agent(tmp_path / "b", "tools: [Read, Task]\ndisallowedTools: # no delegation here\n  - Task # off\n")
    assert block["tools"] == ["Read"]


def test_an_inline_comment_on_permission_mode_still_marks_the_agent_unattended(tmp_path: Path) -> None:
    lines = (
        "permissionMode: bypassPermissions # unattended\n",
        "permissionMode: 'bypassPermissions' # unattended\n",
        'permissionMode: "bypassPermissions"   # unattended\n',
    )
    for index, line in enumerate(lines):
        assert agent(tmp_path / str(index), line)["runs_unattended"] is True


def test_an_inline_comment_on_memory_keeps_the_memory_signal_and_the_off_values(tmp_path: Path) -> None:
    assert agent(tmp_path / "on", "memory: project # keeps notes\n")["persistent_memory"] is True
    assert agent(tmp_path / "off", "memory: off # none\n")["persistent_memory"] is False
    assert agent(tmp_path / "quoted", "memory: 'none' # none\n")["persistent_memory"] is False


def test_a_comment_after_the_name_is_not_sent_in_the_manifest(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/agents/a.md", "---\nname: reviewer # SENTINELCOMMENT\ntools: Read\n---\n")
    manifest = collect(project, tmp_path / "home").manifest
    assert manifest["agents"][0]["name"] == "reviewer"
    assert "SENTINELCOMMENT" not in json.dumps(manifest)


def test_a_hash_without_a_leading_space_or_inside_quotes_is_not_a_comment() -> None:
    parsed = _parse_frontmatter("---\ntools: ['Bash(echo # x)', Read] # c\nname: 'a # b' # c\n---\n", "x.md")
    assert parsed["tools"] == ["Bash(echo # x)", "Read"]
    assert parsed["name"] == "a # b"
    assert _parse_frontmatter("---\nname: a#b\nmemory: \"o\\\\\" # c\n---\n", "x.md") == {"name": "a#b", "memory": "o\\"}


def test_a_comma_inside_quotes_does_not_split_a_tool() -> None:
    parsed = _parse_frontmatter('---\ntools: ["Bash(a, b)", Read]\n---\n', "x.md")
    assert parsed["tools"] == ["Bash(a, b)", "Read"]


# --- unsupported or ambiguous constructs fail closed ------------------------------------------


@pytest.mark.parametrize(
    "construct",
    [
        "tools: [Read,\n  Task]\n",  # flow list continued on the next line
        "tools: [Read, Task\n",  # unclosed bracket
        "tools: Read, Task]\n",  # stray bracket
        "tools: {Task: true}\n",  # flow mapping
        "tools: |\n  Read\n  Task\n",  # block scalar
        "tools: >-\n  Read, Task\n",  # folded block scalar
        "tools: !!seq [Read, Task]\n",  # tag
        "tools: &t [Read, Task]\n",  # anchor
        "tools: *t\n",  # alias
        "tools: Read,\n  Task\n",  # plain scalar continued on the next line
        "tools: 'Read, Task\n",  # unclosed quote
        "tools: \"Read\" Task\n",  # text after a quoted scalar
        "tools: [[Task]]\n",  # nested list
        "tools:\n  - Read\n  - [Task]\n",  # nested list item
        "tools:\n  Read\n",  # indented text that is not a list item
        "tools: Read\ntools: Task\n",  # duplicate key
        "permissionMode: bypassPermissions\n  extra\n",  # continued scalar
        "permissionMode: |\n  bypassPermissions\n",
        "memory: [project]\n",  # a list where a scalar is read
        "memory: {a: b}\n",
        "disallowedTools: [Read\n",
    ],
)
def test_an_unsupported_construct_on_a_read_key_fails_collection(tmp_path: Path, construct: str) -> None:
    message = rejected(tmp_path, construct)
    assert "frontmatter" in message


def test_a_tool_name_that_cannot_be_read_fails_instead_of_being_dropped(tmp_path: Path) -> None:
    assert "tool" in rejected(tmp_path, "tools: [Read, 'Ta sk']\n")


def test_unsupported_constructs_on_keys_that_are_not_read_are_ignored(tmp_path: Path) -> None:
    result = agent(
        tmp_path,
        "description: |\n  tools: Task\n  permissionMode: bypassPermissions\ncolor: [a,\n  b]\nmodel: {x: 1}\ntools: Read\n",
    )
    assert result["tools"] == ["Read"] and result["runs_unattended"] is False


def test_an_empty_tools_value_is_treated_as_not_declared_so_the_agent_inherits(tmp_path: Path) -> None:
    project = tmp_path / "p"
    write(project, ".claude/settings.json", json.dumps({"permissions": {"allow": ["Task"]}}))
    write(project, ".claude/agents/e.md", "---\nname: e\ntools: # none listed\n---\n")
    result = {a["name"]: a for a in collect(project, tmp_path / "home").manifest["agents"]}["e"]
    assert result["can_spawn_subagents"] is True


def test_explicit_empty_tools_list_still_means_no_tools(tmp_path: Path) -> None:
    result = agent(tmp_path, "tools: [] # nothing\n")
    assert result["tools"] == [] and result["can_spawn_subagents"] is False
