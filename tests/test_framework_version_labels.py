"""Tests for scripts/check_framework_version_labels.py (repo-wide v3.1 label guard)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_framework_version_labels as guard  # noqa: E402

PROFILE = ROOT / "skills" / "mcp" / "data" / "mcp-profile-v3.1.json"


def _repo(tmp_path: Path, files: dict[str, str], allow_paths=(), allow_lines=()) -> Path:
    (tmp_path / ".ai-safe2").mkdir()
    (tmp_path / "skills/mcp/data").mkdir(parents=True)
    shutil.copy(PROFILE, tmp_path / "skills/mcp/data/mcp-profile-v3.1.json")
    (tmp_path / ".ai-safe2/version-label-allowlist.json").write_text(json.dumps({
        "paths": [{"glob": g, "reason": "test"} for g in allow_paths],
        "line_patterns": [{"regex": r, "reason": "test"} for r in allow_lines],
    }), encoding="utf-8")
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    return tmp_path


@pytest.mark.parametrize("line", [
    'print("AI SAFE2 v3.0 compliance report")',
    "# Maps to AI SAFE² v3.0 controls",
    "<title>AI SAFE² v3.0 Dashboard</title>",
    "label: AI SAFE2 v3.0 Impact",
    "Each test maps to a specific SAFE2 v3.0 control.",
    "23 New v3.0 Controls",
])
def test_stale_framework_labels_fail(tmp_path, line):
    errors = guard.scan(_repo(tmp_path, {"tool.py": line + "\n"}))
    assert any("[STALE_LABEL]" in e for e in errors), errors


@pytest.mark.parametrize("line", [
    "AI SAFE² v3.1 framework",
    "161 controls, unchanged from AI SAFE² v3.0 in v3.1",   # migration statement
    "Gateway v3.0 component",                             # allowlisted line pattern
    'seed = b"GENESIS:SAFE2:v3.0:CORE"',                  # allowlisted line pattern
    "NEXUS v0.3 and AIM v3.0.1 schema",                   # not a framework label
    "requests>=3.0",
])
def test_current_and_allowlisted_lines_pass(tmp_path, line):
    repo = _repo(tmp_path, {"tool.py": line + "\n"},
                 allow_lines=[r"Gateway v3\.0", r"GENESIS:SAFE2:v3\.0"])
    assert guard.scan(repo) == []


def test_allowlisted_path_passes_and_unused_glob_fails(tmp_path):
    repo = _repo(tmp_path, {"research/001.md": "AI SAFE2 v3.0 research\n"},
                 allow_paths=["research/**", "nowhere/**"])
    errors = guard.scan(repo)
    assert len(errors) == 1 and "[STALE_ALLOWLIST]" in errors[0] and "nowhere/**" in errors[0]


@pytest.mark.parametrize("line,ok", [
    ("See CP.5.MCP-12 (Swarm C2 Detection Controls).", False),
    ("AI SAFE2 v3.1 CP.5.MCP-9 (Context-Tool Isolation)", False),
    ("MCP-8 (Session Economics)", False),
    ("MCP-21 (Anything Here)", False),
    ("AI SAFE2 v3.1 CP.5.MCP-9 (Secret Boundary)", True),
    ("MCP-1 (Command Construction Safety)", True),
    ("MCP-12 (Principal-Scoped State)", True),
    ("MCP-5 (2pts)", True),
    ("MCP-19 (MCP 2026-07-28)", True),
    ("MCP-UPD (Parasitic Toolchain Attack)", True),
])
def test_mcp_control_names_must_be_canonical(tmp_path, line, ok):
    errors = guard.scan(_repo(tmp_path, {"t.py": line + "\n"}))
    assert (errors == []) is ok, errors


def test_reasonless_allowlist_entry_is_a_configuration_error(tmp_path):
    repo = _repo(tmp_path, {"a.py": "x\n"})
    cfg = repo / ".ai-safe2/version-label-allowlist.json"
    cfg.write_text(json.dumps({"paths": [{"glob": "a.py", "reason": " "}], "line_patterns": []}))
    assert guard.main(["--root", str(repo)]) == 2


def test_repository_is_clean():
    assert guard.scan(ROOT) == []
