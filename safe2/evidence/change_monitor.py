"""Bounded, one-shot monitoring for skill and agent configuration changes."""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from safe2.contracts import validate_artifact
from safe2.engines import skill_gate

TRACKED_CONFIGS = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", ".mcp.json", "openclaw.json"}
HARNESS_CONFIG_DIRS = {".codex", ".claude", ".hermes", ".openclaw"}
CONFIG_SUFFIXES = {".json", ".toml", ".yaml", ".yml"}
IGNORED_PARTS = {".git", ".venv", "venv", "node_modules", "__pycache__"}


def _candidate_files(root: Path, max_entries: int) -> list[Path]:
    pending = [root]
    files = []
    traversed = 0
    while pending:
        current = pending.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                traversed += 1
                if traversed > max_entries:
                    raise ValueError("Entry-count limit exceeded; coverage is incomplete")
                if entry.is_symlink():
                    raise ValueError("Symbolic links are not accepted by the change monitor")
                path = Path(entry.path)
                if entry.is_dir(follow_symlinks=False):
                    if entry.name not in IGNORED_PARTS:
                        pending.append(path)
                elif entry.is_file(follow_symlinks=False):
                    files.append(path)
                else:
                    raise ValueError("Special files are not accepted by the change monitor")
    return sorted(files)


def _inventory(root: Path, max_files: int, max_file_bytes: int) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    candidates = _candidate_files(root, max_files)
    skill_roots = [entry.parent for entry in candidates if entry.name == "SKILL.md"]
    for path in candidates:
        relative = path.relative_to(root)
        in_skill = any(skill_root in path.parents for skill_root in skill_roots)
        harness_config = bool(HARNESS_CONFIG_DIRS.intersection(relative.parts)) and path.suffix.lower() in CONFIG_SUFFIXES
        if not in_skill and path.name not in TRACKED_CONFIGS and not harness_config:
            continue
        size = path.stat().st_size
        if size > max_file_bytes:
            raise ValueError("Tracked file size limit exceeded")
        found.append({
            "path": relative.as_posix(), "kind": "skill" if in_skill else "agent_config",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": size,
        })
    return sorted(found, key=lambda item: item["path"])


def monitor(root: Path, baseline: dict[str, Any] | None = None, *, max_files: int = 10_000,
            max_file_bytes: int = 1_000_000) -> dict[str, Any]:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Monitor root must be a directory")
    if baseline is not None and validate_artifact("change-monitor-v1", baseline):
        raise ValueError("Baseline violates the change-monitor contract")
    if baseline is not None and baseline["root"] != root.name:
        raise ValueError("Baseline belongs to a different declared root")
    current = _inventory(root, max_files, max_file_bytes)
    old = {item["path"]: item for item in baseline["inventory"]} if baseline else {}
    new = {item["path"]: item for item in current}
    changes = []
    for path in sorted(set(old) | set(new)):
        if path not in old: change = "added"
        elif path not in new: change = "removed"
        elif old[path]["sha256"] != new[path]["sha256"]: change = "changed"
        else: continue
        changes.append({"path": path, "kind": (new.get(path) or old[path])["kind"], "change": change})

    gates = []
    present_skill_roots = sorted(
        (Path(item["path"]).parent for item in current
         if item["kind"] == "skill" and Path(item["path"]).name == "SKILL.md"),
        key=lambda path: len(path.parts), reverse=True,
    )
    changed_skill_roots = set()
    for item in changes:
        if item["kind"] != "skill":
            continue
        changed_path = Path(item["path"])
        matched = next((candidate for candidate in present_skill_roots
                        if candidate == changed_path.parent or candidate in changed_path.parents), None)
        if matched is not None:
            changed_skill_roots.add(matched.as_posix())
    for relative in sorted(changed_skill_roots):
        findings = skill_gate.scan(root / relative)
        decision, severity = skill_gate.decision_for(findings, strict=False)
        gates.append({"path": relative, "decision": decision, "highest_severity": severity,
                      "findings": len(findings),
                      "coverage": {"files_read": findings.files_read, "text_files": findings.text_files}})
    decision = "reject" if any(item["decision"] == "REJECT" for item in gates) else (
        "hold" if any(item["decision"] == "HOLD FOR REVIEW" for item in gates) or
        any(item["kind"] == "agent_config" for item in changes) else "approve")
    counts = {name: sum(item["change"] == name for item in changes) for name in ("added", "changed", "removed")}
    result = {
        "schema_version": "safe2.change-monitor.v1", "created_at": datetime.now(UTC).isoformat(),
        "root": root.name, "baseline": "validated" if baseline else "not_supplied",
        "inventory": current, "changes": changes, "skill_gates": gates,
        "summary": {"tracked": len(current), **counts, "skills_evaluated": len(gates)},
        "decision": decision, "telemetry": "none", "content_exported": False,
        "conformance_claim": False,
        "limitations": [
            "This one-shot local inventory runs only when invoked and does not install a background service.",
            "Only skill-package files and named or harness-directory agent configuration are tracked.",
            "Skill decisions use bounded static heuristics and are not proof of safety.",
            "Hashes detect byte changes; they do not establish authorship, intent, or execution.",
        ],
    }
    if validate_artifact("change-monitor-v1", result):
        raise ValueError("Change monitor produced an invalid artifact")
    return result
