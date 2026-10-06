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
    # TG-013..TG-022 close gaps measured on 2026-10-06: 9 of 16 hostile skills were
    # APPROVED (env exfil, invisible Unicode, HTML-comment directives, paraphrased
    # and homoglyph injection, JSON-embedded directives, obfuscated execution).
    ("TG-013", "CRITICAL", re.compile(
        r"(?:urlopen|requests\.(?:post|put|get)|httpx\.(?:post|put|get)|fetch|axios\.\w+|"
        r"curl\b|Invoke-WebRequest|socket\.\w+)[^\n]{0,200}(?:os\.environ|process\.env|getenv|\$ENV|env\s*\|)"
        r"|(?:os\.environ|process\.env)[^\n]{0,200}(?:urlopen|requests\.(?:post|put)|httpx\.(?:post|put)|fetch|curl\b)",
        re.IGNORECASE),
     "Environment variables sent to a network endpoint (credential exfiltration)"),
    ("TG-014", "CRITICAL", re.compile("[\U000e0000-\U000e007f‪-‮⁦-⁩]"),
     "Invisible Unicode tag or bidi-override characters (hidden instructions)"),
    ("TG-015", "HIGH", re.compile(
        r"<!--(?:(?!-->)[\s\S]){0,400}?\b(?:assistant|claude|model|agent|llm|ai)\b"
        r"(?:(?!-->)[\s\S]){0,400}?\b(?:always|never|must|run|execute|ignore|silently|do not tell)\b"
        r"(?:(?!-->)[\s\S]){0,400}?-->", re.IGNORECASE),
     "Instruction to the model hidden in an HTML comment"),
    ("TG-016", "CRITICAL", re.compile(
        r"\b(?:set\s+aside|override|supersede|abandon|discard)\s+(?:whatever|all|any|the)?\s*"
        r"(?:(?:the|your)\s+)?(?:operator|user|system|developer|previous|earlier|prior)\b[^\n]{0,80}"
        r"\b(?:told|said|instruct\w*|rules?|prompt|guidance)\b"
        r"|\byour\s+(?:real|true|actual|new)\s+(?:duty|task|job|goal|objective|purpose)\b",
        re.IGNORECASE),
     "Paraphrased instruction override (replaces the operator's instructions)"),
    ("TG-017", "HIGH", re.compile(
        r"\b(?:quietly|silently|secretly|covertly|without\s+(?:telling|informing|notifying))\b"
        r"[^\n.]{0,80}\b(?:upload|send|post|exfiltrate|run|execute|install|delete|copy|forward)\b"
        r"|\b(?:upload|send|post|exfiltrate|run|execute|install|delete|copy|forward)\b[^\n.]{0,80}"
        r"\b(?:quietly|silently|secretly|covertly)\b"
        r"|\b(?:never|do\s+not|don'?t)\s+(?:tell|inform|notify)\s+(?:the\s+)?(?:user|operator|human)\b"
        r"|\b(?:never|do\s+not|don'?t)\s+mention\s+(?:this|it|that)\b",
        re.IGNORECASE),
     "Concealed action: instruction to act without the user knowing"),
    ("TG-018", "CRITICAL", re.compile(
        r"\b(?:you\s+are\s+now|enter|switch\s+to|activate)\s+(?:in\s+)?(?:developer|god|admin|root|DAN|jailbreak|unrestricted)\s+mode\b"
        r"|\bdisable\s+(?:all\s+)?(?:safety|guardrails?|security|content)\s*(?:checks?|filters?|polic(?:y|ies))?\b"
        r"|\bSYSTEM\s*(?:OVERRIDE|:)\s*(?:you|ignore|disable|from\s+now)",
        re.IGNORECASE),
     "Role or safety override directive embedded in skill content or data"),
    ("TG-019", "CRITICAL", re.compile(
        r"__import__\s*\([^)]*\+|importlib\.import_module\s*\([^)]*\+"
        r"|getattr\s*\([^,]+,\s*['\"][^'\"]*['\"]\s*\+|__builtins__\s*(?:\[|\.__dict__)"
        r"|['\"](?:c|cu|cur|w|wg|wge|ev|eva|ex|exe|sy|sys|syst|syste|po|pop|pope)['\"]\s*\+\s*['\"][a-z]{1,4}['\"]"),
     "Obfuscated import, attribute or command name (string concatenation)"),
    ("TG-020", "CRITICAL", re.compile(
        r"https?://\S+\.(?:sh|ps1|py|bash)\b[^\n]{0,160}(?:&&|;|\|\|)\s*(?:ba|z|da)?sh\s+\S+"
        r"|(?:curl|wget)\b[^\n]{0,160}-o\s+(\S+)[^\n]{0,40}(?:&&|;)\s*(?:ba|z|da)?sh\s+\1",
        re.IGNORECASE),
     "Download-then-execute sequence"),
    ("TG-021", "HIGH", re.compile(r"\bshell\s*=\s*True\b|\bos\.(?:system|popen)\s*\(", re.IGNORECASE),
     "Shell command execution from skill code"),
    ("TG-022", "HIGH", re.compile(r"(?:>>|>)\s*~?/?(?:\.bashrc|\.zshrc|\.profile|\.bash_profile)\b|\bcrontab\s+-\s*$|\|\s*crontab\s+-", re.IGNORECASE | re.MULTILINE),
     "Persistence: writes to shell startup files or crontab"),
)

# Latin look-alikes from Cyrillic and Greek. Mixed-script words are normalized and
# re-scanned for the injection rules, so a homoglyph-disguised directive is still
# caught (2026-10-06: "іgnore prevіous іnstructіons" with U+0456 was APPROVED).
_CONFUSABLES = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x",
    "у": "y", "і": "i", "ј": "j", "ѕ": "s", "һ": "h", "ԁ": "d",
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H",
    "О": "O", "Р": "P", "С": "C", "Т": "T", "Х": "X", "І": "I",
    "ο": "o", "α": "a", "ε": "e", "ι": "i", "κ": "k", "ν": "v",
    "ρ": "p", "τ": "t", "υ": "u", "χ": "x", "Ο": "O", "Α": "A",
})
_MIXED_SCRIPT = re.compile(r"\b(?=\w*[A-Za-z])(?=\w*[Ͱ-ϿЀ-ӿ])\w+\b")
_NORMALIZED_RESCAN = {"TG-008", "TG-016", "TG-017", "TG-018"}
_TRIGGER_HIJACK = re.compile(
    r"\b(?:every|all|any)\s+(?:task|request|conversation|prompt)s?\b"
    r"|\balways\s+(?:use|activate|run|load|apply)\b|\bbefore\s+any\s+other\s+skill"
    r"|\b(?:never|do\s+not|don'?t)\s+(?:tell|inform|mention)\b", re.IGNORECASE)
_QUOTED_MENTION = re.compile(r"""["'“‘`]$""")


def _description(text: str) -> tuple[str, int] | None:
    """Return (frontmatter description, line) of a SKILL.md, if present."""
    match = re.match(r"﻿?---\r?\n(.*?)\r?\n---", text, re.S)
    if not match:
        return None
    block = match.group(1)
    found = re.search(r"^description:\s*(?:[>|][-+]?\s*\n)?((?:.+\n?)(?:[ \t]+.+\n?)*)", block, re.M)
    if not found:
        return None
    line = text[: match.start(1) + found.start()].count("\n") + 1
    return " ".join(found.group(1).split()), line


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
        scans = [(text, "")]
        if _MIXED_SCRIPT.search(text):
            line = bisect_right(newlines, _MIXED_SCRIPT.search(text).start()) + 1
            findings.append(GateFinding(
                "TG-023", "HIGH", path.as_posix(), line,
                "Mixed-script word (Latin with Cyrillic/Greek look-alikes): possible homoglyph disguise"))
            scans.append((text.translate(_CONFUSABLES), " [after homoglyph normalization]"))
        if path.name == "SKILL.md":
            desc = _description(text)
            if desc and _TRIGGER_HIJACK.search(desc[0]):
                findings.append(GateFinding(
                    "TG-024", "HIGH", path.as_posix(), desc[1],
                    "Trigger hijack: description claims every task or hides activation from the user"))
        for scanned, suffix in scans:
            for rule_id, severity, pattern, description in RULES:
                if suffix and rule_id not in _NORMALIZED_RESCAN:
                    continue
                for match in pattern.finditer(scanned):
                    if len(findings) >= 10_000:
                        raise ScanLimitExceeded("finding-count limit exceeded; coverage is incomplete")
                    line = bisect_right(newlines, match.start()) + 1
                    detail = description + suffix
                    level = severity
                    if suffix and any(f.rule_id == rule_id and f.line == line for f in findings):
                        continue
                    if (rule_id == "TG-008" and not suffix
                            and _QUOTED_MENTION.search(scanned[max(0, match.start() - 1):match.start()])):
                        # Security prose quoting an attack phrase is held for review, not
                        # auto-rejected. Quoted text is still read by the model, so it is
                        # never approved automatically either.
                        level = "HIGH"
                        detail += " [quoted mention: held for review]"
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
                    findings.append(GateFinding(rule_id, level, path.as_posix(), line, detail))
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
