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


# --- a quote inside a plain specifier is read one way or the collection fails ----------------
#
# Inside a plain entry such as `Bash(echo "*)` a quote is ambiguous: as a literal it ends the
# entry at the first `)`, as an opening quote it swallows every later comma. One reading drops a
# later tool (`Task`), the other turns argument text into tool names. A split is accepted only
# when both readings agree (Codex M1 / Greptile P1 at 53b1b03 and 985501d).


@pytest.mark.parametrize(
    "tools_text",
    [
        'tools: [Read, Bash(git commit -m "msg"), Task]\n',  # balanced quotes: both readings agree
        'tools: Read, Bash(git commit -m "msg"), Task\n',
        'tools: [Bash(echo ")"), Task]\n',
        'tools: [Bash(echo \'x\'), Task] # c\n',
        'tools: ["Bash(echo \\"*)", Task]\n',  # a really quoted item with an escaped quote
        "tools: 'Bash(echo # x), Task'\n",  # a quoted list: `#` is not a comment inside it
        'tools: ["Bash(a, b)", Task]\n',
        'tools:\n  - Bash(echo "x")\n  - Task\n',  # block list items are separate lines
    ],
)
def test_a_quote_inside_a_plain_tool_specifier_is_kept_only_when_it_reads_one_way(
    tmp_path: Path, tools_text: str
) -> None:
    result = agent(tmp_path, tools_text)
    assert result["tools"][-1] == "Task" and "Bash" in result["tools"]
    assert result["can_spawn_subagents"] is True


@pytest.mark.parametrize(
    "construct",
    [
        'tools: [Bash(echo "*), Task]\n',  # Codex M1 / Greptile P1: Task would be swallowed
        'tools: [Bash(echo "*), Task] # c\n',
        'tools: Bash(echo "*), Task\n',
        'tools: Bash(echo "*), Task # c\n',
        "tools: [Bash(echo '*), Task]\n",
        'tools: [Bash(echo "a, b), Task]\n',
        'tools: Bash(echo "), PRIVATE_MARKER, Read(")\n',  # Greptile P1 @ 985501d: argument text as tools
        'tools: [Bash(echo "), PRIVATE_MARKER, Read(")]\n',
        'tools: Bash("), PRIVATE_MARKER, Read(")\n',  # quote right after the parenthesis
        'tools: Bash(echo x"), PRIVATE_MARKER, Read("y)\n',  # quote right after a letter
        "tools: [Bash(echo, Task]\n",  # parenthesis never closes: Task would merge into Bash
        "tools: Bash(echo, Task\n",
        'tools: [Bash(a "(", Task]\n',
        "tools: ['Bash(echo, Task]\n",  # quote that opens an item and never closes
        'tools: [Read, "Bash(echo, Task]\n',
        "tools: 'Bash(echo, Task'\n",
        "tools: [Bash(echo it's), Task]\n",  # a stray apostrophe is rejected too (documented limit)
    ],
)
def test_an_ambiguous_quote_or_parenthesis_in_tools_fails_collection(tmp_path: Path, construct: str) -> None:
    assert "frontmatter" in rejected(tmp_path, construct)


_HEADS = [
    'Bash(echo "*)',
    "Bash(echo '*)",
    'Bash(a "(")',
    'Bash(a ")")',
    'Bash(echo "x',
    "Bash(",
    "Bash)",
    '"Bash(a, b)"',
    "'Bash'",
    'Bash(a, "b")',
    'Bash(a "b", c)',
    "Bash(a # b)",
    'Bash(echo "k")',
    'Bash("k")',
]
_WRAPS = ["[{}, Task]", "{}, Task", "[{}, Task] # c", "[ {} , Task ]", "{}, Task # c"]


@pytest.mark.parametrize("wrap", _WRAPS)
@pytest.mark.parametrize("head", _HEADS)
def test_a_trailing_task_is_never_dropped_silently(head: str, wrap: str) -> None:
    text = f"---\ntools: {wrap.format(head)}\n---\n"
    try:
        parsed = _parse_frontmatter(text, "x.md")
    except ManifestCollectionError:
        return
    assert "Task" in parsed["tools"], parsed["tools"]


_ARGUMENT_HEADS = [
    'Bash(echo "), PRIVATE_MARKER, Read(")',
    'Bash("), PRIVATE_MARKER, Read(")',
    'Bash(echo x"), PRIVATE_MARKER, Read("y)',
    "Bash(echo '), PRIVATE_MARKER, Read(')",
    'Bash(a "b), PRIVATE_MARKER, Read(c")',
    "Bash(a, PRIVATE_MARKER)",
    'Bash(a "), PRIVATE_MARKER, "z")',
]


@pytest.mark.parametrize("wrap", ["[{}, Task]", "{}, Task", "[{}]", "{}", "{} # c"])
@pytest.mark.parametrize("head", _ARGUMENT_HEADS)
def test_text_inside_a_specifier_never_becomes_a_tool_name(head: str, wrap: str) -> None:
    text = f"---\ntools: {wrap.format(head)}\n---\n"
    try:
        parsed = _parse_frontmatter(text, "x.md")
    except ManifestCollectionError:
        return
    assert "PRIVATE_MARKER" not in parsed["tools"], parsed["tools"]


def test_the_closing_delimiter_on_line_200_is_accepted_and_on_line_201_is_rejected() -> None:
    def document(closing_line: int) -> str:
        filler = "".join(f"# filler {index}\n" for index in range(closing_line - 3))
        return f"---\nname: a\n{filler}---\n" if closing_line > 2 else ""

    assert document(200).splitlines()[199] == "---"
    assert _parse_frontmatter(document(200) + "tools: Task\n", "x.md") == {"name": "a"}
    with pytest.raises(ManifestCollectionError, match="closing"):
        _parse_frontmatter(document(201), "x.md")


def test_an_apostrophe_in_a_scalar_value_is_not_rejected_and_its_comment_is_removed() -> None:
    parsed = _parse_frontmatter("---\nname: it's the reviewer # SENTINELCOMMENT\n---\n", "x.md")
    assert parsed == {"name": "it's the reviewer"}


# --- only a `---` at column 0 closes the frontmatter ------------------------------------------


def test_an_indented_rule_inside_a_block_scalar_does_not_close_the_frontmatter() -> None:
    text = "---\nname: a\ndescription: |\n  intro\n  ---\n  more\ntools: Task\npermissionMode: bypassPermissions\n---\nbody\n"
    parsed = _parse_frontmatter(text, "x.md")
    assert parsed == {"name": "a", "tools": ["Task"], "permissionMode": "bypassPermissions"}


def test_an_indented_rule_after_a_read_key_fails_instead_of_dropping_later_fields(tmp_path: Path) -> None:
    assert "frontmatter" in rejected(tmp_path, "tools: [Read]\n  ---\npermissionMode: bypassPermissions\n")


def test_a_closing_delimiter_with_trailing_whitespace_still_closes() -> None:
    assert _parse_frontmatter("---\ntools: Task\n---  \nbody\n", "x.md") == {"tools": ["Task"]}


def test_a_block_list_item_with_an_ambiguous_quote_fails_collection(tmp_path: Path) -> None:
    assert "frontmatter" in rejected(tmp_path, 'tools:\n  - Bash(echo "*)\n  - Task\n')


def test_an_ambiguous_quote_in_disallowed_tools_fails_instead_of_removing_task(tmp_path: Path) -> None:
    message = rejected(tmp_path, 'tools: [Read, Task]\ndisallowedTools: Bash(echo "), Task, Read(")\n')
    assert "frontmatter" in message


# --- a `)` with no matching `(` fails instead of being ignored (Codex L1) ---------------------

_UNMATCHED_CLOSE_FORMS = [
    "{key}: [Bash(echo)), Task]\n",  # flow list
    "{key}: [Bash(echo)), Task] # c\n",
    "{key}: Bash(echo)), Task\n",  # inline comma list
    "{key}: Bash(echo)), Task # c\n",
    "{key}: Bash), Task\n",  # bare name followed by a stray parenthesis
    "{key}: [Read, Bash)]\n",
    "{key}: 'Bash(echo)), Task'\n",  # whole value quoted, split after unquoting
    "{key}:\n  - Bash(echo))\n  - Task\n",  # block list
    "{key}:\n  - Bash(echo)) # c\n  - Task\n",
    "{key}:\n  - Task\n  - Bash)\n",
]


@pytest.mark.parametrize("form", _UNMATCHED_CLOSE_FORMS)
@pytest.mark.parametrize("key", ["tools", "disallowedTools"])
def test_a_close_parenthesis_without_an_open_one_fails_collection(tmp_path: Path, key: str, form: str) -> None:
    message = rejected(tmp_path, form.format(key=key))
    assert "frontmatter" in message and "parenthesis" in message


@pytest.mark.parametrize("form", ["{key}: [Bash(echo, Task]\n", "{key}:\n  - Bash(echo\n  - Task\n"])
@pytest.mark.parametrize("key", ["tools", "disallowedTools"])
def test_an_unclosed_open_parenthesis_fails_in_every_list_form(tmp_path: Path, key: str, form: str) -> None:
    assert "parenthesis" in rejected(tmp_path, form.format(key=key))


@pytest.mark.parametrize(
    "tools_text",
    [
        '["Bash(echo))", Task]',  # a quoted entry may hold anything: quoting is the documented escape
        "[Bash(a (b)), Task]",  # nested parentheses balance
        "[Bash(git commit -m x), Task]",
    ],
)
def test_balanced_or_quoted_parentheses_are_still_accepted(tmp_path: Path, tools_text: str) -> None:
    result = agent(tmp_path, f"tools: {tools_text}\n")
    assert result["tools"][-1] == "Task" and result["can_spawn_subagents"] is True


def test_a_quoted_block_list_entry_may_hold_an_unmatched_parenthesis(tmp_path: Path) -> None:
    result = agent(tmp_path, 'tools:\n  - "Bash(echo))"\n  - Task\n')
    assert result["tools"] == ["Bash", "Task"]


def test_a_parenthesis_in_a_comment_or_a_scalar_is_not_a_tool_entry_problem(tmp_path: Path) -> None:
    assert agent(tmp_path, "tools: [Read, Task] # note)\n")["tools"] == ["Read", "Task"]
    assert _parse_frontmatter("---\nname: reviewer)\n---\n", "x.md") == {"name": "reviewer)"}
