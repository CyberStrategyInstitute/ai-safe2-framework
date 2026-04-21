"""
AI SAFE2 v3.0 Scanner — Rule Base Types
Shared dataclasses and utilities used by all rule modules.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass(frozen=True)
class Rule:
    """
    A single detection rule mapping a pattern or structural check to an AI SAFE2 v3.0 control.

    Attributes:
        control_id:  AI SAFE2 v3.0 control ID (e.g. "S1.5", "CP.10", "P1.T1.2")
        severity:    CRITICAL | HIGH | MEDIUM | LOW | INFO
        description: What was detected
        remediation: What to do about it
        pattern:     Regex string — used for line-by-line scanning (optional)
        check_fn:    Callable(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]
                     Returns list of (line_number, evidence) tuples for structural checks
        file_exts:   File extensions this rule applies to (None = all supported types)
        skip_comments: Whether to skip comment lines (default True)
        min_length:  Minimum line/token length to trigger (avoids false positives)
    """
    control_id: str
    severity: str
    description: str
    remediation: str
    pattern: Optional[str] = None
    check_fn: Optional[Callable] = None
    file_exts: Optional[tuple] = None
    skip_comments: bool = True
    min_length: int = 0

    def __post_init__(self):
        if self.pattern is None and self.check_fn is None:
            raise ValueError(f"Rule {self.control_id}: must have either pattern or check_fn")
        if self.severity not in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
            raise ValueError(f"Rule {self.control_id}: invalid severity '{self.severity}'")


@dataclass
class Finding:
    """
    A single scanner finding. Richer than the v2.1 Violation — includes
    ACT tier applicability, compliance framework hints, and full remediation context.
    """
    control_id: str
    severity: str
    file_path: str
    line_number: int
    evidence: str
    description: str
    remediation: str
    # Populated by the scanner after loading the controls JSON
    control_name: str = ""
    pillar: str = ""
    compliance_frameworks: list = field(default_factory=list)
    act_minimum: list = field(default_factory=list)
    builder_problem: str = ""

    def to_dict(self) -> dict:
        return {
            "control_id": self.control_id,
            "control_name": self.control_name,
            "severity": self.severity,
            "pillar": self.pillar,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "evidence": self.evidence,
            "description": self.description,
            "remediation": self.remediation,
            "compliance_frameworks": self.compliance_frameworks,
            "act_minimum": self.act_minimum,
            "builder_problem": self.builder_problem,
        }


# ── Comment detection helpers ──────────────────────────────────────────────────

def is_comment_line(line: str, filepath: str = "") -> bool:
    """Return True if the line is a comment in a common language."""
    stripped = line.strip()
    if not stripped:
        return True
    ext = filepath.rsplit(".", 1)[-1].lower() if "." in filepath else ""

    # Python / Shell / YAML
    if stripped.startswith("#"):
        return True
    # JavaScript / TypeScript / Java / Go
    if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
        return True
    # HTML / XML
    if stripped.startswith("<!--"):
        return True

    return False


def is_test_file(filepath: str) -> bool:
    """Return True if the file looks like a test file (reduce false positives in tests)."""
    lower = filepath.lower()
    return any(part in lower for part in (
        "/test", "/tests", "/spec", "/specs", "_test.", "_spec.", ".test.", ".spec."
    ))


def extract_string_values(line: str) -> list[str]:
    """Extract string literals from a line for entropy and pattern checks."""
    # Match single-quoted, double-quoted, and template literal strings
    return re.findall(r'["\']([^"\']{8,})["\']|`([^`]{8,})`', line)
