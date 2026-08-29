#!/usr/bin/env python3
"""Repository UX and AI SAFE2 v3.1 documentation consistency checks."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MAJOR_PAGES = [
    "README.md",
    "00-cross-pillar/README.md",
    "01-sanitize-isolate/README.md",
    "02-audit-inventory/README.md",
    "03-fail-safe-recovery/README.md",
    "04-engage-monitor/README.md",
    "05-evolve-educate/README.md",
    "AISM/README.md",
    "NEXUS/README.md",
    "scanner/README.md",
    "gateway/README.md",
    "skills/README.md",
    "skills/mcp/README.md",
    "dashboard/README.md",
]

REQUIRED_DESTINATIONS = (
    "README.md",
    "00-cross-pillar",
    "AISM",
    "NEXUS",
)

# Current framework-facing statements may not advertise v3.0 as current.
# Component pages can retain an older component version when they also identify
# AI SAFE2 v3.1 as the current framework, for example Gateway v3.0.
STALE_CURRENT_PATTERNS = (
    re.compile(r"^#\s+AI SAFE²? Framework v3\.0\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"\bPart of the AI SAFE²? v3\.0 Ecosystem\b", re.IGNORECASE),
    re.compile(r"\bFramework:\s*AI SAFE²?\s*v3\.0\b", re.IGNORECASE),
    re.compile(r"\bcurrent framework(?: version)?\s*[:=]?\s*v3\.0\b", re.IGNORECASE),
)


def check_page(path: Path) -> list[str]:
    errors: list[str] = []
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")

    if "../cross-pillar/" in text or "](cross-pillar/" in text:
        errors.append(f"{rel}: uses obsolete cross-pillar path; use 00-cross-pillar")

    if rel != "README.md":
        for destination in REQUIRED_DESTINATIONS:
            if destination not in text:
                errors.append(f"{rel}: missing navigation/reference to {destination}")

    for pattern in STALE_CURRENT_PATTERNS:
        if pattern.search(text):
            errors.append(f"{rel}: advertises AI SAFE2 v3.0 as the current framework")
            break

    if rel != "README.md" and "F6921E" not in text.upper():
        errors.append(f"{rel}: missing standard AI SAFE2 release color #F6921E")

    return errors


def main() -> int:
    errors: list[str] = []
    for rel in MAJOR_PAGES:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"{rel}: required major landing page is missing")
            continue
        errors.extend(check_page(path))

    # Broken canonical-path check applies to every Markdown file in the repo.
    for path in ROOT.rglob("*.md"):
        if any(part in {".git", ".venv", "node_modules"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "../cross-pillar/" in text or "](cross-pillar/" in text:
            rel = path.relative_to(ROOT).as_posix()
            errors.append(f"{rel}: obsolete cross-pillar navigation path")

    if errors:
        print("Repository UX check FAILED")
        for error in sorted(set(errors)):
            print(f" - {error}")
        return 1

    print("Repository UX check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
