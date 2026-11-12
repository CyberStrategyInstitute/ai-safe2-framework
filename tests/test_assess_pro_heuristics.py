"""The flag heuristics live in a data file so a reviewer can read and sign them."""

from __future__ import annotations

import json
from importlib.resources import files

import pytest

from safe2.pro.heuristics import (
    CATEGORIES,
    HeuristicsError,
    load_heuristics,
    parse_heuristics,
    tool_tokens,
)

CASES = {
    "Task": {"spawn"},
    "Agent": {"spawn"},
    "mcp__orchestrator__spawn_worker": {"spawn"},
    "mcp__todo__create_task": set(),  # `task` is an exact name only, never a token
    "mcp__gmail__send_email": {"send"},
    "mcp__slack__postMessage": {"send"},
    "mcp__slack__read_channel": {"send"},  # conservative: a messaging server is treated as a sender
    "mcp__postgres__query": set(),  # `postgres` is not the token `post`
    "mcp__stripe__create_charge": {"money"},
    "mcp__bank__transfer_funds": {"money"},
    "mcp__memory__store": {"memory"},
    "mcp__mem0__add": {"memory"},
    "Bash": {"exec"},
    "Edit": {"write"},
    "Write": {"write"},
    "mcp__files__delete_file": {"delete"},
    "WebFetch": set(),
    "Read": set(),
    "Grep": set(),
}


@pytest.mark.parametrize(("tool", "expected"), sorted(CASES.items()))
def test_tool_name_categories(tool: str, expected: set[str]) -> None:
    assert set(load_heuristics().categorize(tool)) == expected


def test_tokenization_splits_punctuation_and_camel_case() -> None:
    assert tool_tokens("mcp__slack__postMessage") == {"mcp", "slack", "post", "message"}
    assert tool_tokens("send-email.v2") == {"send", "email", "v2"}


def test_packaged_heuristics_define_every_category_and_every_undetectable_flag() -> None:
    heuristics = load_heuristics()
    assert heuristics.data["status"] == "draft-unreviewed"
    assert set(heuristics.data["tool_categories"]) == set(CATEGORIES)
    assert set(heuristics.data["cannot_detect"]) == {
        "mandate_configured",
        "memory_provenance",
        "budget_ceiling_configured",
    }
    assert set(heuristics.approval_categories) <= {
        "before_write", "before_exec", "before_send", "before_payment", "before_delete",
    }
    assert len(heuristics.digest) == 64


def test_heuristics_fail_closed_when_structurally_invalid() -> None:
    raw = files("safe2.data").joinpath("pro-manifest-heuristics-v1.json").read_bytes()
    document = json.loads(raw)
    parse_heuristics(raw)
    broken = json.loads(raw)
    del broken["tool_categories"]["money"]
    with pytest.raises(HeuristicsError):
        parse_heuristics(json.dumps(broken).encode())
    wrong_version = dict(document, schema_version="safe2.pro-manifest-heuristics.v0")
    with pytest.raises(HeuristicsError):
        parse_heuristics(json.dumps(wrong_version).encode())
    with pytest.raises(HeuristicsError):
        parse_heuristics(b"not json")
    bad_pattern = json.loads(raw)
    bad_pattern["secret_patterns"]["assignment"] = "(unclosed"
    with pytest.raises(HeuristicsError):
        parse_heuristics(json.dumps(bad_pattern).encode())
