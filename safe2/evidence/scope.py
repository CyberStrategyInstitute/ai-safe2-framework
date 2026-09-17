"""Metadata-only assessment scope inventory bound to an agent-system identity."""

from __future__ import annotations

import fnmatch
import hashlib
import os
import stat
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from safe2.challenge.io import parse_json, safe_path
from safe2.contracts import validate_artifact

MAX_SOURCE_BYTES = 1_000_000


def _validate_pattern(pattern: str) -> None:
    path = PurePosixPath(pattern)
    if (
        "\\" in pattern
        or "\x00" in pattern
        or pattern.startswith("/")
        or ":" in pattern
        or ".." in path.parts
    ):
        raise ValueError("Scope patterns must be normalized relative POSIX globs")


def _load(payload: bytes, contract: str, label: str) -> dict[str, Any]:
    if not payload or len(payload) > MAX_SOURCE_BYTES:
        raise ValueError(f"{label} must be a nonempty file of at most 1 MB")
    value = parse_json(payload)
    if validate_artifact(contract, value):
        raise ValueError(f"{label} violates its evidence contract")
    return value


def _identity(payload: bytes) -> dict[str, Any]:
    return _load(payload, "system-identity-manifest-v1", "System identity manifest")


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(
        (getattr(info, "st_file_attributes", 0) or 0) & 0x400
    )


def _matches(relative: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(relative, pattern)


def _raise_walk_error(error: OSError) -> None:
    raise error


def _entry(relative: str, rules: list[dict[str, Any]], default: dict[str, Any], kind: str) -> tuple[dict[str, Any], list[str]]:
    matched = [rule for rule in rules if any(_matches(relative, pattern) for pattern in rule["patterns"])]
    conflicts: list[str] = []
    if matched:
        selected = matched[0]
        semantics = {(rule["classification"], rule["disposition"], tuple(rule["component_ids"])) for rule in matched}
        if len(semantics) > 1:
            conflicts = [rule["rule_id"] for rule in matched]
        classification = selected["classification"]
        disposition = selected["disposition"]
        component_ids = selected["component_ids"]
        rationale = selected["rationale"]
        rule_ids = [rule["rule_id"] for rule in matched]
    else:
        classification = default["classification"]
        disposition = default["disposition"]
        component_ids = []
        rationale = default["rationale"]
        rule_ids = []
    if kind == "unsafe_link":
        classification, disposition = "unknown", "partial"
        component_ids = []
        rationale = "Symbolic link or reparse point was inventoried but not followed."
    return {
        "path": relative,
        "kind": kind,
        "classification": classification,
        "disposition": disposition,
        "component_ids": component_ids,
        "rule_ids": rule_ids,
        "rationale": rationale,
        "metadata_only": True,
    }, conflicts


def build(
    source_payload: bytes,
    identity_payload: bytes,
    project_root: str | Path,
    *,
    max_entries: int = 10_000,
) -> dict[str, Any]:
    """Build a bounded path inventory without reading repository file contents."""
    if not 1 <= max_entries <= 10_000:
        raise ValueError("max_entries must be between 1 and 10000")
    source = _load(source_payload, "assessment-scope-source-v1", "Assessment scope source")
    identity = _identity(identity_payload)
    if source["subject"]["subject_id"] != identity["subject"]["subject_id"]:
        raise ValueError("Assessment scope subject does not match system identity")
    if source["subject"]["system_fingerprint_sha256"] != identity["system_fingerprint_sha256"]:
        raise ValueError("Assessment scope fingerprint does not match system identity")

    component_ids = {item["component_id"] for item in identity["components"]}
    requested_components = set(source["deployment_subject"]["component_ids"])
    if not requested_components <= component_ids:
        raise ValueError("Deployment subject references an unknown system component")
    rule_ids: set[str] = set()
    for rule in source["rules"]:
        if rule["rule_id"] in rule_ids:
            raise ValueError("Scope rule identifiers must be unique")
        rule_ids.add(rule["rule_id"])
        if not set(rule["component_ids"]) <= component_ids:
            raise ValueError("Scope rule references an unknown system component")
        for pattern in rule["patterns"]:
            _validate_pattern(pattern)

    root = safe_path(project_root)
    root_info = root.lstat()
    if not stat.S_ISDIR(root_info.st_mode):
        raise ValueError("Project root must be a directory")

    entries: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    truncated = False
    for directory, directory_names, file_names in os.walk(
        root, followlinks=False, onerror=_raise_walk_error
    ):
        directory_path = Path(directory)
        safe_directories = []
        for name in sorted(directory_names):
            child = directory_path / name
            info = child.lstat()
            if _is_link(info):
                if len(entries) >= max_entries:
                    truncated = True
                    break
                item, rule_conflicts = _entry(_relative(root, child), source["rules"], source["default"], "unsafe_link")
                entries.append(item)
                if rule_conflicts:
                    conflicts.append({"path": item["path"], "rule_ids": rule_conflicts})
            else:
                safe_directories.append(name)
        directory_names[:] = safe_directories
        if truncated:
            break
        for name in sorted(file_names):
            if len(entries) >= max_entries:
                truncated = True
                break
            child = directory_path / name
            info = child.lstat()
            if _is_link(info):
                kind = "unsafe_link"
            elif stat.S_ISREG(info.st_mode):
                kind = "file"
            else:
                raise ValueError("Project root contains an unsupported non-regular path")
            item, rule_conflicts = _entry(_relative(root, child), source["rules"], source["default"], kind)
            entries.append(item)
            if rule_conflicts:
                conflicts.append({"path": item["path"], "rule_ids": rule_conflicts})
        if truncated:
            break

    entries.sort(key=lambda item: item["path"])
    conflicts.sort(key=lambda item: item["path"])
    dispositions = Counter(item["disposition"] for item in entries)
    classifications = Counter(item["classification"] for item in entries)
    unsafe_links = sum(item["kind"] == "unsafe_link" for item in entries)
    recommendations = []
    if classifications["unknown"]:
        recommendations.append(f"Classify {classifications['unknown']} path(s) currently governed by the default unknown rule.")
    if conflicts:
        recommendations.append(f"Resolve {len(conflicts)} path classification conflict(s); first matching rule is retained only for inventory.")
    if unsafe_links:
        recommendations.append(f"Review {unsafe_links} symbolic link or reparse path(s) that were not followed.")
    if truncated:
        recommendations.append("Increase the bounded entry limit or narrow the project root; inventory coverage is truncated.")
    if not entries:
        recommendations.append("Confirm the project root; no file or unsafe-link entries were inventoried.")

    result = {
        "schema_version": "safe2.assessment-scope-manifest.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "source": {
            "scope_id": source["scope_id"],
            "declared_at": source["declared_at"],
            "sha256": hashlib.sha256(source_payload).hexdigest(),
            "bytes": len(source_payload),
            "system_identity_sha256": hashlib.sha256(identity_payload).hexdigest(),
            "authentication": "not_checked",
        },
        "subject": source["subject"],
        "deployment_subject": source["deployment_subject"],
        "root": {"display_name": root.name or "project-root", "path_disclosed": False},
        "entries": entries,
        "conflicts": conflicts,
        "summary": {
            "files": sum(item["kind"] == "file" for item in entries),
            "unsafe_links": unsafe_links,
            "conflicts": len(conflicts),
            "truncated": truncated,
            "included": dispositions["included"],
            "excluded": dispositions["excluded"],
            "partial": dispositions["partial"],
            "not_applicable": dispositions["not_applicable"],
            "unclassified": classifications["unknown"],
            "classifications": dict(sorted(classifications.items())),
        },
        "recommendations": recommendations,
        "decision_scope": "assessment_scope_inventory_only",
        "scope_verified": False,
        "content_inspected": False,
        "conformance_claim": False,
        "limitations": [
            "Path classification follows declared glob rules and is not an independent verification of deployment scope.",
            "Only path metadata is inventoried; file contents, runtime loading, build inclusion, and execution are not inspected.",
            "The source and identity hashes bind submitted bytes but do not authenticate their authors or claims.",
            "Included, excluded, partial, and not-applicable labels do not establish control effectiveness or AI SAFE2 conformance.",
            "The first rule supplies inventory fields when conflicting rules match; every conflict remains explicit and blocks strict success.",
        ],
    }
    if validate_artifact("assessment-scope-manifest-v1", result):
        raise ValueError("Assessment scope builder produced an invalid manifest")
    return result
