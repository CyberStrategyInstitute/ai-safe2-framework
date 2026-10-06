"""
AI SAFE2 v3.1 Scanner rule base types.
Shared dataclasses and utilities used by all rule modules.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

RuleCheck = Callable[[str, list[str], str], list[tuple[int, str]]]


@dataclass(frozen=True)
class Rule:
    """A detection rule mapped to an AI SAFE2 control or profile control.

    Attributes:
        control_id: Framework or profile control ID, for example S1.5, CP.10, MCP-19.
        severity: CRITICAL | HIGH | MEDIUM | LOW | INFO.
        description: What was detected.
        remediation: What to do about it.
        pattern: Regex used for line-by-line scanning, when applicable.
        check_fn: Callable(content, lines, filepath) returning (line_number, evidence) tuples.
        file_exts: Extensions this rule applies to, or None for all supported types.
        skip_comments: Whether to skip comment lines.
        min_length: Minimum line/token length to trigger.
    """

    control_id: str
    severity: str
    description: str
    remediation: str
    pattern: str | None = None
    check_fn: RuleCheck | None = None
    file_exts: tuple[str, ...] | None = None
    skip_comments: bool = True
    min_length: int = 0

    def __post_init__(self) -> None:
        if self.pattern is None and self.check_fn is None:
            raise ValueError(f"Rule {self.control_id}: must have either pattern or check_fn")
        if self.severity not in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
            raise ValueError(f"Rule {self.control_id}: invalid severity '{self.severity}'")


@dataclass
class Finding:
    """A scanner finding enriched with control and governance metadata."""

    control_id: str
    severity: str
    file_path: str
    line_number: int
    evidence: str
    description: str
    remediation: str
    control_name: str = ""
    pillar: str = ""
    compliance_frameworks: list[str] = field(default_factory=list)
    act_minimum: list[str] = field(default_factory=list)
    builder_problem: str = ""

    def to_dict(self) -> dict[str, Any]:
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


def is_comment_line(line: str, filepath: str = "") -> bool:
    """Return True if the line is a comment in a common language."""
    stripped = line.strip()
    if not stripped:
        return True

    if stripped.startswith("#"):
        return True
    if stripped.startswith(("//", "/*", "*")):
        return True
    return bool(stripped.startswith("<!--"))


_TEST_DIRS = {"test", "tests", "spec", "specs", "__tests__", "testdata", "fixtures"}


def is_test_file(filepath: str) -> bool:
    """Return True if the file looks like a test file.

    Pass a path RELATIVE to the scan root. Matching is by whole path segment or
    test-file naming convention. The previous substring check on the absolute path
    treated every file under e.g. /srv/testbed/ or ~/test-env/ as a test file and
    suppressed all non-critical findings, including secret detection.
    """
    parts = [p for p in filepath.replace("\\", "/").lower().split("/") if p]
    if not parts:
        return False
    *dirs, name = parts
    return (
        any(d in _TEST_DIRS for d in dirs)
        or name.startswith("test_")
        or any(tag in name for tag in ("_test.", "_spec.", ".test.", ".spec."))
    )


def extract_string_values(line: str) -> list[str]:
    """Extract string literals from a line for entropy and pattern checks."""
    values: list[str] = []
    for match in re.finditer(r'(["\'])(.{8,}?)\1|`([^`]{8,})`', line):
        value = match.group(2) or match.group(3)
        if value:
            values.append(value)
    return values
