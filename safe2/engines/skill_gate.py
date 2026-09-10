"""Skill Trust Gate engine.

Absorbed from scripts/skill_trust_gate.py as part of the safe2 CLI
consolidation. The hardened engine scans content regardless of filename;
`safe2 scan skill` and `safe2 gate skill` share this implementation.

The gate is intentionally narrow: it looks for executable or
credential-handling patterns that should not appear as operational
instructions in a distributable skill package. Security prose that merely
names attack classes is not rejected.
"""
from __future__ import annotations

import re
from bisect import bisect_right
from ipaddress import ip_address
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlsplit

from safe2.bounded_files import inventory
from safe2.challenge.io import read_bytes, safe_path

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
    # TG-007..TG-012 close the executable-payload gap. Before these, a byte-identical
    # payload was CRITICAL as payload.md and invisible as payload.sh, because script
    # extensions were outside TEXT_EXTENSIONS. See test_skill_gate_engine.py.
    ("TG-007", "CRITICAL", re.compile(r"\b(?:eval|exec)\s*\(\s*(?:os\.environ|request|input|urlopen|base64\.b64decode)", re.IGNORECASE),
     "Dynamic execution of externally controlled input"),
    ("TG-008", "CRITICAL", re.compile(r"(?:ignore|disregard|forget)\s+(?:all\s+)?(?:your\s+|the\s+)?previous\s+instructions", re.IGNORECASE),
     "Prompt-injection directive embedded in skill content"),
    ("TG-009", "HIGH", re.compile(r"(?:\.ssh/id_[a-z0-9_]+|\.aws/credentials|\.config/gh/hosts\.yml|\.netrc|\.docker/config\.json)", re.IGNORECASE),
     "Reference to a credential-bearing local path"),
    ("TG-010", "HIGH", re.compile(r"https?://(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?/", re.IGNORECASE),
     "Hardcoded raw-IP network endpoint"),
    ("TG-011", "HIGH", re.compile(r"\b(?:AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{36}|xox[baprs]-[A-Za-z0-9-]{10,})\b"),
     "Hardcoded credential or API key material"),
    ("TG-012", "HIGH", re.compile(r"base64[^\n]{0,40}\|\s*curl|curl[^\n]{0,80}(?:-d\s*@-|--data-binary\s*@-)", re.IGNORECASE),
     "Encoded local data piped to a network endpoint"),
)

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


class ScanFindings(list[GateFinding]):
    """List-compatible findings with explicit inspected-content coverage."""

    files_read: int = 0
    text_files: int = 0
    bytes_read: int = 0


def scan(root: Path, *, max_files: int = 10_000, max_file_bytes: int = 5_000_000,
         max_total_bytes: int = 100_000_000) -> ScanFindings:
    """Static-scan a skill package directory for trust-gate violations."""
    findings = ScanFindings()
    if min(max_files, max_file_bytes, max_total_bytes) < 1:
        raise ScanLimitExceeded("scan limits must be positive")
    try:
        root = safe_path(root)
        if not root.is_dir():
            raise ValueError("root must be a directory")
    except (OSError, ValueError) as exc:
        raise ScanLimitExceeded("unsafe or unavailable scan root; coverage is incomplete") from exc
    total = 0
    try:
        paths = inventory(root, max_entries=max_files)
    except (OSError, ValueError) as exc:
        raise ScanLimitExceeded("unsafe inventory or entry-count limit; coverage is incomplete") from exc
    for path in paths:
        try:
            data = read_bytes(path, limit=min(max_file_bytes, max_total_bytes - total))
        except (OSError, ValueError) as exc:
            raise ScanLimitExceeded("file could not be safely read within byte limits; coverage is incomplete") from exc
        total += len(data)
        findings.files_read += 1
        findings.bytes_read = total
        if total > max_total_bytes:
            raise ScanLimitExceeded("skill scan exceeded the total-byte limit; coverage is incomplete")
        try:
            encoding = "utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
            text = data.decode(encoding)
            if "\x00" in text:
                raise UnicodeError("binary content")
        except UnicodeError:
            findings.append(GateFinding("TG-COVERAGE", "HIGH", path.as_posix(), 1,
                                        "Binary or unsupported encoding: not inspected; manual review required"))
            continue
        findings.text_files += 1
        newlines = [match.start() for match in re.finditer("\n", text)]
        for rule_id, severity, pattern, description in RULES:
            for match in pattern.finditer(text):
                if len(findings) >= 10_000:
                    raise ScanLimitExceeded("finding-count limit exceeded; coverage is incomplete")
                line = bisect_right(newlines, match.start()) + 1
                detail = description
                relative = path.relative_to(root)
                if (any(part.lower() in {"tests", "test", "__tests__", "fixtures", "testdata"}
                        for part in relative.parts[:-1]) or relative.name.lower().startswith("test_")):
                    detail += " [test-like path: inspect usage; severity retained because paths are untrusted]"
                if rule_id == "TG-010":
                    try:
                        address = ip_address(urlsplit(match.group()).hostname or "")
                        kind = ("loopback" if address.is_loopback else "link-local" if address.is_link_local
                                else "private/non-global" if not address.is_global else "public")
                        detail += f" [{kind} endpoint: context required; address class is not authorization]"
                    except ValueError:
                        detail += " [invalid IP literal: inspect context]"
                findings.append(GateFinding(rule_id, severity, path.as_posix(), line, detail))
    if findings.text_files == 0 and not findings:
        findings.append(GateFinding("TG-COVERAGE", "HIGH", root.as_posix(), 1,
                                    "Empty package: no files inspected; manual review required"))
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
