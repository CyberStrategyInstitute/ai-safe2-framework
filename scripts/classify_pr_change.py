#!/usr/bin/env python3
"""Route a change to proportionate solution, framework, or content review."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

ROUTE_LABELS = {
    "review:solution": "solution",
    "review:framework": "framework",
    "review:content": "content",
}

SOLUTION_PREFIXES = (
    ".github/",
    ".ai-safe2/",
    ".semgrep/",
    "aisafe2_mcp_tools/",
    "challenges/",
    "config/",
    "dashboard/",
    "examples/",
    "gateway/",
    "nexus/",
    "safe2/",
    "scanner/",
    "scripts/",
    "skills/",
    "tests/",
)
SOLUTION_NAMES = {
    ".gitleaks.toml",
    ".pr_agent.toml",
    "agents.md",
    "pyproject.toml",
}
SOLUTION_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".mjs",
    ".ps1",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".sql",
    ".ts",
    ".tsx",
}
FRAMEWORK_PREFIXES = (
    "00-cross-pillar/",
    "01-sanitize-isolate/",
    "02-audit-inventory/",
    "03-fail-safe-recovery/",
    "04-engage-monitor/",
    "05-evolve-educate/",
    "aism/",
    "docs/engineering/",
    "forge-act/",
)
CONTENT_PREFIXES = ("assets/", "research/", "releases/", "resources/")
CONTENT_EXTENSIONS = {
    ".avif",
    ".bmp",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".svg",
    ".webp",
}
TEXT_EXTENSIONS = {".md", ".mdx", ".rst", ".txt"}
IDENTIFIER = re.compile(
    r"\b(?:AI[- ]?SAFE2|SAFE2|AISM|EFA|NEXUS|P[1-5]|CP)[-_. :]*[A-Z0-9][A-Z0-9_.-]*\b",
    re.IGNORECASE,
)
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\)")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def changed_paths(root: Path, base: str, head: str) -> list[str]:
    return sorted(
        line.replace("\\", "/")
        for line in _git(root, "diff", "--name-only", f"{base}...{head}").splitlines()
        if line
    )


def classify(paths: list[str], labels: list[str] | None = None) -> dict[str, Any]:
    normalized = [path.replace("\\", "/") for path in paths]
    lowered = [path.lower() for path in normalized]
    requested = {ROUTE_LABELS[label.lower()] for label in (labels or []) if label.lower() in ROUTE_LABELS}
    if len(requested) > 1:
        raise ValueError("Only one review:solution, review:framework, or review:content label may be used.")

    solution = sorted(
        path
        for path, low in zip(normalized, lowered)
        if low in SOLUTION_NAMES
        or low.startswith(SOLUTION_PREFIXES)
        or Path(low).suffix in SOLUTION_EXTENSIONS
        or Path(low).name in {"dockerfile", "makefile"}
    )
    framework = sorted(
        path for path, low in zip(normalized, lowered) if low.startswith(FRAMEWORK_PREFIXES)
    )
    content = sorted(
        path
        for path, low in zip(normalized, lowered)
        if low.startswith(CONTENT_PREFIXES)
        or Path(low).suffix in CONTENT_EXTENSIONS
        or (Path(low).suffix in TEXT_EXTENSIONS and low not in framework)
    )

    override = next(iter(requested), None)
    if solution:
        route = "solution"
        reason = "Executable code, tests, automation, configuration, or enforcement policy changed."
        if override and override != route:
            reason += f" The {override} label cannot lower a detected solution change."
    elif override:
        route = override
        reason = f"The PR explicitly selected the {override} review route."
    elif framework:
        route = "framework"
        reason = "Normative framework or development-method material changed without solution code."
    else:
        route = "content"
        reason = "Only editorial, research, link, image, or other non-solution material changed."

    return {
        "schema_version": "ai-safe2.change-route.v1",
        "route": route,
        "full_review_required": route == "solution",
        "pr_agent_required": route == "solution",
        "greptile_eligible": route == "solution",
        "compliance_posture": "full_candidate" if route == "solution" else "partially_compliant",
        "reason": reason,
        "labels": labels or [],
        "paths": normalized,
        "detected": {"solution": solution, "framework": framework, "content": content},
    }


def lightweight_validation(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    if result["route"] != "content":
        return {"required": False, "status": "not_applicable", "missing_local_references": []}
    checked: list[str] = []
    missing: list[dict[str, str]] = []
    for relative in result["paths"]:
        path = root / relative
        if not path.is_file():
            continue  # Deletion is a valid content change and has no links to inspect.
        checked.append(relative)
        if path.suffix.lower() not in {".md", ".mdx"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for target in MARKDOWN_LINK.findall(text):
            clean = target.strip("<>").split("#", 1)[0]
            if not clean or re.match(r"^(?:[a-z]+:|//|#)", clean, re.IGNORECASE):
                continue
            candidate = (path.parent / clean).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                missing.append({"source": relative, "target": target})
                continue
            if not candidate.exists():
                missing.append({"source": relative, "target": target})
    return {
        "required": True,
        "status": "passed" if not missing else "failed",
        "checked_paths": checked,
        "missing_local_references": missing,
        "scope": "Changed content files and their local Markdown targets only.",
    }


def framework_impact(root: Path, base: str, head: str, result: dict[str, Any]) -> dict[str, Any]:
    if result["route"] != "framework":
        return {"required": False, "status": "not_applicable", "references": [], "identifiers": []}
    changed = set(result["paths"])
    tokens: set[str] = set()
    for path in changed:
        tokens.add(Path(path).stem.lower())
        if Path(path).suffix.lower() in TEXT_EXTENSIONS:
            diff = _git(root, "diff", "--unified=0", f"{base}...{head}", "--", path)
            for line in diff.splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    tokens.update(match.group(0).lower() for match in IDENTIFIER.finditer(line))
                    if line.startswith("+#"):
                        heading = re.sub(r"^\+#+\s*", "", line).strip().lower()
                        if len(heading) >= 8:
                            tokens.add(heading)
    tokens = {token for token in tokens if len(token) >= 4}
    references: list[dict[str, Any]] = []
    searchable = TEXT_EXTENSIONS | {".json", ".yaml", ".yml"}
    for candidate in root.rglob("*"):
        relative = candidate.relative_to(root).as_posix()
        if (
            not candidate.is_file()
            or relative in changed
            or candidate.suffix.lower() not in searchable
            or any(part in {".git", ".venv", ".uv-cache", ".pytest_cache"} for part in candidate.parts)
        ):
            continue
        try:
            text = candidate.read_text(encoding="utf-8").lower()
        except (OSError, UnicodeDecodeError):
            continue
        matched = sorted(token for token in tokens if token in text)
        if matched:
            references.append({"path": relative, "matched_identifiers": matched[:10]})
    return {
        "required": True,
        "status": "human_impact_confirmation_required" if references else "contained_change_candidate",
        "changed_framework_paths": sorted(changed),
        "identifiers": sorted(tokens),
        "references": references[:100],
        "references_truncated": len(references) > 100,
        "claim_boundary": "Reference discovery identifies possible dependencies; it does not prove semantic consistency.",
    }


def render(result: dict[str, Any]) -> str:
    impact = result["framework_impact"]
    lines = [
        "# Proportionate Change Review",
        "",
        f"**Route:** `{result['route']}` · **Compliance posture:** `{result['compliance_posture']}`",
        "",
        result["reason"],
        "",
    ]
    if result["route"] == "solution":
        lines += [
            "PR-Agent and the optional strategic Greptile status check apply. Deterministic CI remains authoritative.",
        ]
    elif result["route"] == "content":
        lines += [
            "Only changed-artifact and normal deterministic validation apply. Whole-repository AI review is intentionally skipped.",
            f"Lightweight validation: `{result['lightweight_validation']['status']}`.",
        ]
        for row in result["lightweight_validation"]["missing_local_references"]:
            lines.append(f"- Missing local target `{row['target']}` referenced by `{row['source']}`")
    else:
        lines += [
            "## Framework impact",
            "",
            f"Impact status: `{impact['status']}`",
            "",
        ]
        if impact["references"]:
            lines += ["Possible existing dependencies not changed in this PR:", ""]
            lines.extend(f"- `{row['path']}`" for row in impact["references"])
        else:
            lines.append("No textual cross-references were discovered outside the changed files.")
        lines += [
            "",
            impact["claim_boundary"],
            "A named human must confirm whether discovered dependencies require aligned edits before merge.",
        ]
    lines += ["", "## Changed paths", ""]
    lines.extend(f"- `{path}`" for path in result["paths"])
    return "\n".join(lines) + "\n"


def _labels(value: str | None) -> list[str]:
    if not value:
        return []
    parsed = json.loads(value)
    if parsed is None:
        return []
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError("--labels-json must be a JSON array of strings")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--labels-json")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    result = classify(changed_paths(root, args.base, args.head), _labels(args.labels_json))
    result["framework_impact"] = framework_impact(root, args.base, args.head, result)
    result["lightweight_validation"] = lightweight_validation(root, result)
    payload = json.dumps(result, indent=2) + "\n"
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(payload, encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render(result), encoding="utf-8")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a", encoding="utf-8") as handle:
            handle.write(f"route={result['route']}\n")
            handle.write(f"full_review_required={str(result['full_review_required']).lower()}\n")
            handle.write(f"compliance_posture={result['compliance_posture']}\n")
            handle.write(
                f"validation_passed={str(result['lightweight_validation']['status'] != 'failed').lower()}\n"
            )
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
