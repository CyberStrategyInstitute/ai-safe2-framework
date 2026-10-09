#!/usr/bin/env python3
"""Validate repository AI SAFE2 workflow invariants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = {"policy_may_raise_not_lower_risk", "evidence_revision_bound", "provider_failure_is_not_pass", "human_authorizes_merge_release_and_risk"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    path = args.root.resolve() / ".ai-safe2" / "workflow.json"
    try:
        workflow = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    errors = []
    if workflow.get("schema_version") != "ai-safe2.developer-workflow.v1": errors.append("unsupported schema")
    if set(workflow.get("routes", {})) != {"standard", "enhanced", "critical"}: errors.append("invalid routes")
    for name in REQUIRED:
        if workflow.get("invariants", {}).get(name) is not True: errors.append(f"missing invariant: {name}")
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("AI SAFE2 repository workflow validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

