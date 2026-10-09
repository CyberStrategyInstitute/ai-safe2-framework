#!/usr/bin/env python3
"""Reject feature and release PR descriptions that omit decision context."""

from __future__ import annotations

import argparse
import re


BASELINE_GROUPS = {
    "decision summary": ("decision summary", "summary", "outcome"),
    "problem": ("problem", "why", "why it matters"),
    "scope": ("scope and included changes", "scope", "included", "main changes", "changes"),
    "validation": ("evidence and testing", "validation", "evidence", "hosted evidence and ci status"),
    "owner decision": ("owner decision and residual risk", "owner decision", "authority", "human authority"),
}

MATERIAL_GROUPS = {
    "boundaries": (
        "security and evidence boundaries",
        "product boundaries",
        "product and evidence boundaries",
        "product and security boundaries",
        "security review notes",
        "technology contribution and claim boundaries",
    ),
    "compatibility and recovery": ("compatibility and recovery", "compatibility", "rollback", "recovery"),
    "deferred work": ("deferred and post-merge work", "follow-on work", "after merge", "deferred"),
}


def headings(body: str) -> set[str]:
    return {
        re.sub(r"\s+", " ", match.group(1).strip().lower())
        for line in body.splitlines()
        if (match := re.match(r"^#{1,6}\s+(.+?)\s*$", line))
    }


def validate(*, title: str, body: str, author: str = "") -> list[str]:
    if author.lower().endswith("[bot]") or title.lower().startswith(("build(deps):", "chore(deps):")):
        return []

    errors: list[str] = []
    if "\\n" in body:
        errors.append("description contains literal \\n escapes instead of Markdown line breaks")
    found = headings(body)
    for label, alternatives in BASELINE_GROUPS.items():
        if not any(item in found for item in alternatives):
            errors.append(f"missing decision section: {label}")

    material = title.lower().startswith(("feat", "release", "fix", "security"))
    if material:
        for label, alternatives in MATERIAL_GROUPS.items():
            if not any(item in found for item in alternatives):
                errors.append(f"missing material-change section: {label}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--author", default="")
    args = parser.parse_args()
    errors = validate(title=args.title, body=args.body, author=args.author)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("Pull request description includes the required decision context.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
