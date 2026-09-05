"""Skill Trust Gate engine.

Absorbed from scripts/skill_trust_gate.py as part of the safe2 CLI
consolidation (PART 3, AI SAFE2/MCP family). Logic is unchanged from the
original script; it is now an importable engine instead of a standalone
argparse script, so `safe2 scan skill` and `safe2 gate skill` can share it.

The gate is intentionally narrow: it looks for executable or
credential-handling patterns that should not appear as operational
instructions in a distributable skill package. Security prose that merely
names attack classes is not rejected.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import NamedTuple

RULES = (
    ("TG-001", "CRITICAL", re.compile(r"curl\s+[^\n|]+\|\s*(?:sh|bash)\b", re.IGNORECASE),
     "Remote download piped directly to a shell"),
    ("TG-002", "CRITICAL", re.compile(r"wget\s+[^\n|]+\|\s*(?:sh|bash)\b", re.IGNORECASE),
     "Remote download piped directly to a shell"),
    ("TG-003", "CRITICAL", re.compile(r"\brm\s+-rf\s+/(?:\s|$)", re.IGNORECASE),
     "Destructive root filesystem command"),
    ("TG-004", "CRITICAL", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
     "Embedded private key material"),
    ("TG-005", "HIGH", re.compile(r"(?:cat|type)\s+[^\n]*(?:\.ssh|\.aws|\.env|credentials)", re.IGNORECASE),
     "Instruction reads credential-bearing local files"),
    ("TG-006", "HIGH", re.compile(r"(?:powershell|pwsh)\s+[^\n]*(?:-enc|-encodedcommand)\b", re.IGNORECASE),
     "Encoded PowerShell execution"),
)

TEXT_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".json", ".toml"}
EXCLUDED_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "build", "dist", "__pycache__"}


class ScanLimitExceeded(RuntimeError):
    """The skill scan stopped because complete bounded coverage was impossible."""


class GateFinding(NamedTuple):
    rule_id: str
    severity: str
    file: str
    line: int
    description: str

    def as_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "file": self.file,
            "line": self.line,
            "description": self.description,
        }


def scan(root: Path, *, max_files: int = 10_000, max_file_bytes: int = 5_000_000,
         max_total_bytes: int = 100_000_000) -> list[GateFinding]:
    """Static-scan a skill package directory for trust-gate violations."""
    findings: list[GateFinding] = []
    count = 0
    total = 0
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(
            name for name in dirs
            if name not in EXCLUDED_DIRS and not name.startswith((".test-temp", "pytest-"))
        )
        for name in sorted(files):
            path = Path(current) / name
            if path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            count += 1
            if count > max_files:
                raise ScanLimitExceeded("skill scan exceeded the file-count limit; coverage is incomplete")
            size = path.stat().st_size
            if size > max_file_bytes:
                raise ScanLimitExceeded(f"skill file exceeds the per-file byte limit: {path}")
            total += size
            if total > max_total_bytes:
                raise ScanLimitExceeded("skill scan exceeded the total-byte limit; coverage is incomplete")
            text = path.read_text(encoding="utf-8", errors="replace")
            for rule_id, severity, pattern, description in RULES:
                for match in pattern.finditer(text):
                    line = text.count("\n", 0, match.start()) + 1
                    findings.append(GateFinding(rule_id, severity, path.as_posix(), line, description))
    return findings


def decision_for(findings: list[GateFinding], strict: bool) -> tuple[str, str]:
    """Return (decision, highest_severity) for a set of findings.

    decision is one of APPROVE, HOLD FOR REVIEW, REJECT.
    """
    severities = {f.severity for f in findings}
    if "CRITICAL" in severities:
        return "REJECT", "CRITICAL"
    if "HIGH" in severities:
        return ("REJECT" if strict else "HOLD FOR REVIEW"), "HIGH"
    return "APPROVE", "NONE"


# Exit-code contract shared with safe2.commands.gate — see that module's
# module docstring for the full rationale.
DECISION_EXIT_CODES = {
    "APPROVE": 0,
    "HOLD FOR REVIEW": 2,
    "REJECT": 1,
}
