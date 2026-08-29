#!/usr/bin/env python3
"""Validate a minimal AI SAFE² skill trust manifest."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REQUIRED_FIELDS = (
    "Skill Name",
    "Framework Version",
    "Owner",
    "Purpose",
    "Network Access",
    "Credential Access",
    "Execution Capability",
    "Data Persistence",
    "Review Status",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("card")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = Path(args.card)
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    present = {}
    for field in REQUIRED_FIELDS:
        present[field] = bool(re.search(rf"^\s*[-*]?\s*\*\*{re.escape(field)}:\*\*\s*\S+", text, re.MULTILINE))

    valid = all(present.values()) and "v3.1" in text
    completeness = round(100 * sum(present.values()) / len(REQUIRED_FIELDS))
    result = {
        "valid": valid,
        "completeness_score": completeness,
        "framework_version_present": "v3.1" in text,
        "fields": present,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"valid={valid} completeness={completeness}%")
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
