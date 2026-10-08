#!/usr/bin/env python3
"""Classify changed paths without invoking a model or external service."""

from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path


def matches(path: str, pattern: str) -> bool:
    path = path.replace("\\", "/").lower()
    pattern = pattern.replace("\\", "/").lower()
    return fnmatch.fnmatchcase(path, pattern) or (
        pattern.startswith("**/") and fnmatch.fnmatchcase(path, pattern[3:])
    )


def classify(paths: list[str], profile: dict) -> dict:
    critical = sorted(path for path in paths if any(matches(path, pattern) for pattern in profile["critical_patterns"]))
    enhanced = sorted(path for path in paths if any(matches(path, pattern) for pattern in profile["enhanced_patterns"]))
    if critical:
        route = "critical"
        matched = critical
    elif enhanced:
        route = "enhanced"
        matched = enhanced
    else:
        route = "standard"
        matched = []
    return {"schema_version":"ai-safe2.change-route.v1","route":route,"profile":profile["profile_id"],"paths":sorted(paths),"matched_paths":matched,"review_lenses":profile["lenses"],"merge_authorized":False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--paths-json", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = classify(json.loads(args.paths_json), json.loads(args.profile.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

