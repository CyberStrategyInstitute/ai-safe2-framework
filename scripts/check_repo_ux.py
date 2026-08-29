#!/usr/bin/env python3
"""Repository UX and AI SAFE² v3.1 documentation consistency checks."""
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
    "examples/README.md",
    "research/README.md",
]

REQUIRED_DESTINATIONS = (
    "README.md",
    "00-cross-pillar",
    "AISM",
    "NEXUS",
)

TOP_START = "<!-- AI-SAFE2-UX:START -->"
TOP_END = "<!-- AI-SAFE2-UX:END -->"
BOTTOM_START = "<!-- AI-SAFE2-UX-FOOTER:START -->"
BOTTOM_END = "<!-- AI-SAFE2-UX-FOOTER:END -->"

# Current framework-facing statements may not advertise v3.0 as current.
# Component pages can retain an older component version when they also identify
# AI SAFE² v3.1 as the current framework, for example Gateway v3.0.
STALE_CURRENT_PATTERNS = (
    re.compile(r"^#\s+AI SAFE²? Framework v3\.0\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"\bPart of the AI SAFE²? v3\.0 Ecosystem\b", re.IGNORECASE),
    re.compile(r"\bFramework:\s*AI SAFE²?\s*v3\.0\b", re.IGNORECASE),
    re.compile(r"\bcurrent framework(?: version)?\s*[:=]?\s*v3\.0\b", re.IGNORECASE),
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def check_page(path: Path) -> list[str]:
    errors: list[str] = []
    rel = path.relative_to(ROOT).as_posix()
    text = read(path)

    if "../cross-pillar/" in text or "](cross-pillar/" in text:
        errors.append(f"{rel}: uses obsolete cross-pillar path; use 00-cross-pillar")

    if rel != "README.md":
        for destination in REQUIRED_DESTINATIONS:
            if destination not in text:
                errors.append(f"{rel}: missing navigation/reference to {destination}")

    for pattern in STALE_CURRENT_PATTERNS:
        if pattern.search(text):
            errors.append(f"{rel}: advertises AI SAFE² v3.0 as the current framework")
            break

    if rel != "README.md" and "F6921E" not in text.upper():
        errors.append(f"{rel}: missing standard AI SAFE² release color #F6921E")

    return errors


def check_surface_shell(path: Path, *, index_label: str) -> list[str]:
    errors: list[str] = []
    rel = path.relative_to(ROOT).as_posix()
    text = read(path)

    for marker in (TOP_START, TOP_END, BOTTOM_START, BOTTOM_END):
        if text.count(marker) != 1:
            errors.append(f"{rel}: expected exactly one {marker} marker")

    required = (
        "F6921E",
        "820F1A",
        "808080",
        "Framework Home",
        "00-cross-pillar",
        index_label,
        "AI SAFE² v3.1",
    )
    for token in required:
        if token not in text:
            errors.append(f"{rel}: missing standardized surface token/reference {token}")
    return errors


def check_examples() -> list[str]:
    errors: list[str] = []
    paths = sorted((ROOT / "examples").glob("*/README.md"))
    if not paths:
        return ["examples/: no example README surfaces found"]

    for path in paths:
        errors.extend(check_surface_shell(path, index_label="Examples Index"))

    # Guard two metadata defects found during the v3.1 sweep so the generated
    # index cannot silently regress to unrelated copied metadata.
    metadata_expectations = {
        "langflow-sovereign-runtime": ("<!-- stack: Langflow -->", "Langflow visual builder"),
        "slowmist-overlay": ("<!-- stack: SlowMist / OpenClaw -->", "SlowMist OpenClaw security practices"),
    }
    for folder, expected in metadata_expectations.items():
        path = ROOT / "examples" / folder / "README.md"
        text = read(path)
        for token in expected:
            if token not in text:
                errors.append(f"{path.relative_to(ROOT).as_posix()}: incorrect example metadata; missing {token}")

    return errors


def check_research() -> list[str]:
    errors: list[str] = []
    notes = sorted((ROOT / "research").glob("[0-9][0-9][0-9]_*.md"))
    if len(notes) < 24:
        errors.append(f"research/: expected at least 24 numbered research notes, found {len(notes)}")

    for path in notes:
        errors.extend(check_surface_shell(path, index_label="Research Index"))

    index_path = ROOT / "research" / "README.md"
    if not index_path.exists():
        errors.append("research/README.md: research index is missing")
        return errors

    index_text = read(index_path)
    for path in notes:
        if f"./{path.name}" not in index_text:
            errors.append(f"research/README.md: missing index entry for {path.name}")

    if chr(0x2014) in index_text or chr(0x2013) in index_text:
        errors.append("research/README.md: generated index contains em/en dash characters")
    return errors


def main() -> int:
    errors: list[str] = []
    for rel in MAJOR_PAGES:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"{rel}: required major landing page is missing")
            continue
        errors.extend(check_page(path))

    errors.extend(check_examples())
    errors.extend(check_research())

    # Broken canonical-path check applies to every Markdown file in the repo.
    for path in ROOT.rglob("*.md"):
        if any(part in {".git", ".venv", "node_modules"} for part in path.parts):
            continue
        text = read(path)
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
