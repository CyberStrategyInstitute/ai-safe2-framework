#!/usr/bin/env python3
"""Validate the release package or a repository using its stable contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_INVARIANTS = {
    "policy_may_raise_not_lower_risk",
    "evidence_revision_bound",
    "provider_failure_is_not_pass",
    "human_authorizes_merge_release_and_risk",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_workflow(root: Path) -> list[str]:
    errors: list[str] = []
    candidates = [
        root / ".ai-safe2" / "workflow.json",
        root / "repository-template" / ".ai-safe2" / "workflow.json",
    ]
    workflow_path = next((path for path in candidates if path.exists()), None)
    if workflow_path is None:
        return ["missing .ai-safe2/workflow.json"]
    workflow = load(workflow_path)
    if workflow.get("schema_version") != "ai-safe2.developer-workflow.v1":
        errors.append("unsupported workflow schema_version")
    if workflow.get("minimum_cli_version") != "1.0.1":
        errors.append("minimum_cli_version must be pinned to 1.0.1 for this release")
    routes = workflow.get("routes", {})
    if set(routes) != {"standard", "enhanced", "critical"}:
        errors.append("routes must contain standard, enhanced, and critical")
    invariants = workflow.get("invariants", {})
    for name in REQUIRED_INVARIANTS:
        if invariants.get(name) is not True:
            errors.append(f"required invariant is not true: {name}")
    for route in ("enhanced", "critical"):
        if routes.get(route, {}).get("semantic_review") != "required":
            errors.append(f"{route} must require semantic review")
    if routes.get("critical", {}).get("security_review") != "required":
        errors.append("critical must require security review")
    return errors


def validate_package(root: Path) -> list[str]:
    errors = validate_workflow(root)
    json_paths = sorted(root.rglob("*.json"))
    for path in json_paths:
        try:
            load(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {path.relative_to(root)}: {exc}")
    manifests_path = root / "adapters" / "manifests.json"
    if manifests_path.exists():
        manifests = load(manifests_path)
        ids = [item.get("adapter_id") for item in manifests]
        if len(ids) != len(set(ids)):
            errors.append("adapter ids must be unique")
        for manifest in manifests:
            if "authorize" in manifest.get("authority", []):
                errors.append(f"adapter may not authorize: {manifest.get('adapter_id')}")
            required_states = {"unavailable", "failed", "produced"}
            if not required_states.issubset(set(manifest.get("failure_states", []))):
                errors.append(f"adapter lacks failure truth: {manifest.get('adapter_id')}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    errors = validate_package(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("AI SAFE2 Developer Workflow contracts validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

