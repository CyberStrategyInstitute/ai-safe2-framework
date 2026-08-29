#!/usr/bin/env python3
"""Normalize AI SAFE² v3.1 navigation shells for examples and research notes.

This script deliberately does not rewrite technical bodies. It adds or refreshes
bounded UX blocks so historical findings, publication dates, component versions,
and implementation details remain intact while repository navigation and current
framework context stay consistent. Existing line-ending style is preserved.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
RESEARCH = ROOT / "research"

TOP_START = "<!-- AI-SAFE2-UX:START -->"
TOP_END = "<!-- AI-SAFE2-UX:END -->"
BOTTOM_START = "<!-- AI-SAFE2-UX-FOOTER:START -->"
BOTTOM_END = "<!-- AI-SAFE2-UX-FOOTER:END -->"

BADGE_VERSION = "https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square"
BADGE_EXAMPLE = "https://img.shields.io/badge/Surface-Example-820F1A?style=flat-square"
BADGE_RESEARCH = "https://img.shields.io/badge/Surface-Research-820F1A?style=flat-square"
BADGE_CONTEXT = "https://img.shields.io/badge/Context-v3.1_Current-808080?style=flat-square"

EXAMPLE_METADATA_OVERRIDES = {
    "langflow-sovereign-runtime": (
        "Langflow",
        "Sovereign runtime defense package for the Langflow visual builder.",
    ),
    "slowmist-overlay": (
        "SlowMist / OpenClaw",
        "Threat-intelligence overlay mapping SlowMist OpenClaw security practices to AI SAFE² controls.",
    ),
}


def read_exact(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def write_exact(path: Path, text: str) -> None:
    path.write_bytes(text.encode("utf-8"))


def newline_for(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def adapt_newlines(block: str, newline: str) -> str:
    return block.replace("\r\n", "\n").replace("\n", newline)


def replace_or_insert(text: str, start: str, end: str, block: str, *, prepend: bool) -> str:
    newline = newline_for(text)
    block = adapt_newlines(block, newline)
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if pattern.search(text):
        return pattern.sub(lambda _: block, text, count=1)
    stripped = text.lstrip("\ufeff")
    if prepend:
        return block + newline + newline + stripped
    return stripped.rstrip() + newline + newline + block + newline


def apply_example_metadata_override(path: Path, text: str) -> str:
    override = EXAMPLE_METADATA_OVERRIDES.get(path.parent.name)
    if not override:
        return text
    stack, description = override
    newline = newline_for(text)
    stack_line = f"<!-- stack: {stack} -->"
    desc_line = f"<!-- description: {description} -->"
    if re.search(r"<!--\s*stack:\s*.+?\s*-->", text, re.IGNORECASE):
        text = re.sub(r"<!--\s*stack:\s*.+?\s*-->", stack_line, text, count=1, flags=re.IGNORECASE)
    else:
        text = stack_line + newline + text
    if re.search(r"<!--\s*description:\s*.+?\s*-->", text, re.IGNORECASE):
        text = re.sub(r"<!--\s*description:\s*.+?\s*-->", desc_line, text, count=1, flags=re.IGNORECASE)
    else:
        text = desc_line + newline + text
    return text


def example_top() -> str:
    return f"""{TOP_START}
[![AI SAFE² v3.1]({BADGE_VERSION})](../../README.md)
[![Surface: Example]({BADGE_EXAMPLE})](../README.md)
[![Context: v3.1 Current]({BADGE_CONTEXT})](../../docs/REPOSITORY-UX-STANDARD.md)

[Framework Home](../../README.md) | [Examples Index](../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [AISM](../../AISM/) | [NEXUS](../../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

> **Current framework context:** AI SAFE² v3.1. This example may preserve historical component versions or earlier framework references where they describe when the implementation was created. For current conformance, use the v3.1 framework and applicable profile requirements.
{TOP_END}"""


def example_footer() -> str:
    return f"""{BOTTOM_START}
---

### Repository navigation

[Examples Index](../README.md) | [Framework Home](../../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [NEXUS](../../NEXUS/) | [Scanner](../../scanner/README.md) | [MCP Profile](../../00-cross-pillar/cp5_mcp_server_security.md)

*AI SAFE² v3.1 | Cyber Strategy Institute*
{BOTTOM_END}"""


def research_top() -> str:
    return f"""{TOP_START}
[![AI SAFE² v3.1]({BADGE_VERSION})](../README.md)
[![Surface: Research]({BADGE_RESEARCH})](./README.md)
[![Context: v3.1 Current]({BADGE_CONTEXT})](../docs/REPOSITORY-UX-STANDARD.md)

[Framework Home](../README.md) | [Research Index](./README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

> **Current framework context:** AI SAFE² v3.1. This research note preserves its original publication date, evidence, and historical framework references. Use current v3.1 normative control and profile documents for implementation or conformance decisions.
{TOP_END}"""


def research_footer(previous_name: str | None, next_name: str | None) -> str:
    sequence = []
    if previous_name:
        sequence.append(f"[Previous research note](./{previous_name})")
    sequence.append("[Research Index](./README.md)")
    if next_name:
        sequence.append(f"[Next research note](./{next_name})")
    sequence_line = " | ".join(sequence)
    return f"""{BOTTOM_START}
---

### Research navigation

{sequence_line}

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [NEXUS](../NEXUS/) | [Challenge Lab](../challenges/)

*AI SAFE² v3.1 | Cyber Strategy Institute*
{BOTTOM_END}"""


def normalize_examples() -> list[Path]:
    changed: list[Path] = []
    for path in sorted(EXAMPLES.glob("*/README.md")):
        original = read_exact(path)
        text = apply_example_metadata_override(path, original)
        text = replace_or_insert(text, TOP_START, TOP_END, example_top(), prepend=True)
        text = replace_or_insert(text, BOTTOM_START, BOTTOM_END, example_footer(), prepend=False)
        if text != original:
            write_exact(path, text)
            changed.append(path)
    return changed


def research_notes() -> list[Path]:
    return sorted(
        [p for p in RESEARCH.glob("[0-9][0-9][0-9]_*.md") if p.name != "README.md"],
        key=lambda p: p.name,
    )


def extract_title(path: Path) -> str:
    text = read_exact(path)
    match = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    title = match.group(1).strip() if match else path.stem.replace("_", " ")
    title = title.replace("|", "-")
    title = title.replace(chr(0x2014), "-").replace(chr(0x2013), "-")
    return title


def build_research_index(notes: list[Path]) -> str:
    rows = []
    for path in notes:
        number = path.name.split("_", 1)[0]
        rows.append(f"| {number} | [{extract_title(path)}](./{path.name}) | Original publication context preserved; interpret current implementation guidance through v3.1 |")
    table = "\n".join(rows)
    return f"""# AI SAFE² Research Index
### Evidence, threat analysis, and framework foundations

[![AI SAFE² v3.1]({BADGE_VERSION})](../README.md)
[![Surface: Research]({BADGE_RESEARCH})](./README.md)
[![Context: v3.1 Current]({BADGE_CONTEXT})](../docs/REPOSITORY-UX-STANDARD.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Challenge Lab](../challenges/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

## How to read the research library

The research library records the evidence and reasoning that informed AI SAFE² over time. Individual notes retain their original publication dates, terminology, findings, and historical framework references so the evidence trail remains inspectable.

**Current normative context is AI SAFE² v3.1.** Historical research does not override the current framework, CP.5 profile, MCP specification binding, or current conformance requirements.

For MCP implementation decisions, use the [CP.5.MCP v3.1 profile](../00-cross-pillar/cp5_mcp_server_security.md) and MCP `2026-07-28` semantics.

---

## Research notes

| Note | Research article | Current-use guidance |
|---|---|---|
{table}

---

## Repository navigation

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Examples](../examples/) | [Challenge Lab](../challenges/)

*AI SAFE² v3.1 | Cyber Strategy Institute*
"""


def normalize_research() -> list[Path]:
    changed: list[Path] = []
    notes = research_notes()
    for index, path in enumerate(notes):
        previous_name = notes[index - 1].name if index > 0 else None
        next_name = notes[index + 1].name if index + 1 < len(notes) else None
        original = read_exact(path)
        text = replace_or_insert(original, TOP_START, TOP_END, research_top(), prepend=True)
        text = replace_or_insert(
            text,
            BOTTOM_START,
            BOTTOM_END,
            research_footer(previous_name, next_name),
            prepend=False,
        )
        if text != original:
            write_exact(path, text)
            changed.append(path)

    index_path = RESEARCH / "README.md"
    index_text = build_research_index(notes)
    previous = read_exact(index_path) if index_path.exists() else ""
    if index_text != previous:
        write_exact(index_path, index_text)
        changed.append(index_path)
    return changed


def main() -> int:
    changed = normalize_examples() + normalize_research()
    print(f"Normalized {len(changed)} documentation surface(s).")
    for path in changed:
        print(path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
