#!/usr/bin/env python3
"""Static trust gate for AI SAFE² skill packages.

DEPRECATED: this logic has been absorbed into the safe2 CLI as
`safe2 gate skill <path>` / `safe2 scan skill <path>` (see safe2/engines/skill_gate.py
and MIGRATION.md). This script is kept working, unchanged, for anyone with
existing automation calling it directly — but new usage should go through
`safe2`, which has one exit-code contract shared across scan/gate/score/
report/mcp instead of this script's own narrow 0/2 codes.

The gate is intentionally narrow: it looks for executable or credential-handling
patterns that should not appear as operational instructions in a distributable
skill package. Security prose that merely names attack classes is not rejected.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RULES = (
    ("TG-001", "CRITICAL", re.compile(r"curl\s+[^\n|]+\|\s*(?:sh|bash)\b", re.IGNORECASE), "Remote download piped directly to a shell"),
    ("TG-002", "CRITICAL", re.compile(r"wget\s+[^\n|]+\|\s*(?:sh|bash)\b", re.IGNORECASE), "Remote download piped directly to a shell"),
    ("TG-003", "CRITICAL", re.compile(r"\brm\s+-rf\s+/(?:\s|$)", re.IGNORECASE), "Destructive root filesystem command"),
    ("TG-004", "CRITICAL", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "Embedded private key material"),
    ("TG-005", "HIGH", re.compile(r"(?:cat|type)\s+[^\n]*(?:\.ssh|\.aws|\.env|credentials)", re.IGNORECASE), "Instruction reads credential-bearing local files"),
    ("TG-006", "HIGH", re.compile(r"(?:powershell|pwsh)\s+[^\n]*(?:-enc|-encodedcommand)\b", re.IGNORECASE), "Encoded PowerShell execution"),
)

TEXT_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".json", ".toml"}


def scan(root: Path) -> list[dict]:
    findings: list[dict] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for rule_id, severity, pattern, description in RULES:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append({
                    "rule_id": rule_id,
                    "severity": severity,
                    "file": path.as_posix(),
                    "line": line,
                    "description": description,
                })
    return findings


def decision_for(findings: list[dict], strict: bool) -> tuple[str, str]:
    severities = {item["severity"] for item in findings}
    if "CRITICAL" in severities:
        return "REJECT", "CRITICAL"
    if "HIGH" in severities:
        return ("REJECT" if strict else "HOLD FOR REVIEW"), "HIGH"
    return "APPROVE", "NONE"


def main() -> int:
    print("NOTE: scripts/skill_trust_gate.py is deprecated — use `safe2 gate skill` "
          "or `safe2 scan skill` instead. Behavior here is unchanged for now.", file=sys.stderr)
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_path")
    parser.add_argument("--output", choices=("json", "markdown", "both"), default="both")
    parser.add_argument("--report", required=True)
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = Path(args.skill_path)
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Skill path does not exist or is not a directory: {root}")

    findings = scan(root)
    decision, severity = decision_for(findings, args.strict)
    report = {
        "scanner": "AI SAFE2 Skill Trust Gate",
        "scanner_version": "1.1.0",
        "framework_version": "v3.1",
        "skill_path": root.as_posix(),
        "decision": decision,
        "severity": severity,
        "aism_level": "L3-static",
        "findings": findings,
    }

    prefix = Path(args.report)
    if args.output in {"json", "both"}:
        prefix.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.output in {"markdown", "both"}:
        lines = [
            "# AI SAFE² Skill Trust Gate Report",
            "",
            "- Framework: v3.1",
            f"- Decision: {decision}",
            f"- Highest severity: {severity}",
            f"- Skill path: `{root.as_posix()}`",
            "",
            "## Findings",
            "",
        ]
        if findings:
            for item in findings:
                lines.append(
                    f"- {item['severity']} {item['rule_id']}: {item['file']}:{item['line']} - {item['description']}"
                )
        else:
            lines.append("No static trust-gate findings.")
        prefix.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0 if decision == "APPROVE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
