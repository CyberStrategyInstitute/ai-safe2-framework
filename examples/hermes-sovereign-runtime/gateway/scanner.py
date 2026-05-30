#!/usr/bin/env python3
"""
AI SAFE² Scanner — Hermes Sovereign Runtime
Cyber Strategy Institute · AI SAFE² v3.0

Scans Hermes Agent's skills, memory stores, plugins, and dependencies for:
  - Malicious skill patterns (supply chain attacks)
  - Memory injection artifacts (persistent prompt injection)
  - Unpinned git dependencies (supply chain substitution)
  - Credential patterns written to memory
  - Unsigned or unreviewed skill imports
  - Git dependency integrity

AI SAFE² Controls implemented:
  P2.A-C01 — Skill manifest validation
  P2.A-C02 — Dependency pinning verification
  P2.A-C03 — Credential inventory
  P4.M-C02 — Memory audit daemon

Usage:
  python3 scanner.py                          # Full scan
  python3 scanner.py --skills                 # Skills only
  python3 scanner.py --memory                 # Memory only
  python3 scanner.py --deps                   # Dependencies only
  python3 scanner.py --strict                 # Fail on any HIGH or above
  python3 scanner.py --watch                  # Continuous mode (runs hourly)
  python3 scanner.py --target /custom/path    # Custom target path
"""

import argparse
import ast
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


# ─── Data Types ──────────────────────────────────────────────────────────────

Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]


@dataclass
class Finding:
    severity: Severity
    category: str
    target: str
    description: str
    remediation: str
    control_id: str  # AI SAFE² control reference


@dataclass
class ScanResult:
    scanned_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    findings: list[Finding] = field(default_factory=list)
    targets_scanned: int = 0
    scan_duration_ms: int = 0

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "CRITICAL")

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "HIGH")

    @property
    def passed(self) -> bool:
        return self.critical_count == 0

    def to_dict(self) -> dict:
        return {
            "scanned_at": self.scanned_at,
            "summary": {
                "targets_scanned": self.targets_scanned,
                "total_findings": len(self.findings),
                "critical": self.critical_count,
                "high": self.high_count,
                "passed": self.passed,
            },
            "findings": [
                {
                    "severity": f.severity,
                    "category": f.category,
                    "target": f.target,
                    "description": f.description,
                    "remediation": f.remediation,
                    "control": f.control_id,
                }
                for f in self.findings
            ],
        }


# ─── Patterns ─────────────────────────────────────────────────────────────────

SKILL_DANGEROUS_PATTERNS = [
    (re.compile(r"subprocess\.(?:Popen|run|call|check_output)\s*\("), "CRITICAL",
     "subprocess execution", "Skill executes shell subprocesses — arbitrary code execution risk"),
    (re.compile(r"(?:import|from)\s+subprocess"), "HIGH",
     "subprocess import", "Skill imports subprocess module"),
    (re.compile(r"os\.system\s*\("), "CRITICAL",
     "os.system call", "Skill calls os.system — command injection vector"),
    (re.compile(r"eval\s*\("), "CRITICAL",
     "eval() call", "Skill uses eval() — arbitrary code execution"),
    (re.compile(r"exec\s*\("), "CRITICAL",
     "exec() call", "Skill uses exec() — arbitrary code execution"),
    (re.compile(r"__import__\s*\("), "HIGH",
     "dynamic import", "Skill uses dynamic __import__"),
    (re.compile(r"requests\.(?:get|post|put|delete|patch)\s*\("), "HIGH",
     "outbound HTTP", "Skill makes outbound HTTP calls — potential exfiltration"),
    (re.compile(r"socket\.connect\s*\("), "HIGH",
     "raw socket", "Skill opens raw sockets — potential C2 channel"),
    (re.compile(r"open\s*\([^)]*['\"]w['\"]"), "MEDIUM",
     "file write", "Skill opens files for writing — check target path"),
    (re.compile(r"(?:~/.ssh|/.aws|credentials|api.key|\.env)", re.IGNORECASE), "CRITICAL",
     "credential path", "Skill references credential file paths"),
    (re.compile(r"base64\.(?:b64decode|decodebytes)\s*\("), "MEDIUM",
     "base64 decode", "Skill decodes base64 — potential obfuscation"),
    (re.compile(r"(?:curl|wget|nc|ncat|netcat|nmap)", re.IGNORECASE), "HIGH",
     "network tool", "Skill invokes network utility — potential exfiltration"),
    (re.compile(r"https?://(?!api\.hermes\.|localhost|127\.0\.0\.1)[a-zA-Z0-9.\-]+"),
     "MEDIUM", "external URL", "Skill contains external URL reference"),
]

MEMORY_INJECTION_PATTERNS = [
    (re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?", re.IGNORECASE),
     "CRITICAL", "injection_ignore_instructions"),
    (re.compile(r"(?:your\s+)?new\s+system\s+prompt\s+is", re.IGNORECASE),
     "CRITICAL", "injection_new_system_prompt"),
    (re.compile(r"you\s+are\s+now\s+(?:a\s+)?(?:different|unrestricted|jailbroken)", re.IGNORECASE),
     "CRITICAL", "injection_identity_replacement"),
    (re.compile(r"disregard\s+(?:your\s+)?(?:safety\s+)?guidelines?", re.IGNORECASE),
     "HIGH", "injection_safety_bypass"),
    (re.compile(r"developer\s+mode\s+(?:enabled|active)", re.IGNORECASE),
     "HIGH", "injection_developer_mode"),
    (re.compile(r"do\s+anything\s+now|DAN\s+mode", re.IGNORECASE),
     "CRITICAL", "injection_dan"),
    # Credential patterns in memory
    (re.compile(r"sk-ant-[a-zA-Z0-9\-_]{20,}"),
     "CRITICAL", "credential_anthropic_key"),
    (re.compile(r"sk-(?:proj-)?[a-zA-Z0-9]{32,}"),
     "CRITICAL", "credential_openai_key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"),
     "CRITICAL", "credential_aws_access_key"),
    (re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"),
     "CRITICAL", "credential_private_key"),
    (re.compile(r"gh[pos]_[A-Za-z0-9]{36}"),
     "CRITICAL", "credential_github_token"),
]

PINNED_DEP_PATTERN = re.compile(
    r"(?:git\+https?://|git://)[^@\s]+@([a-fA-F0-9]{40})"
)


# ─── Scanners ────────────────────────────────────────────────────────────────

def scan_skills(skills_dir: Path) -> list[Finding]:
    findings = []
    if not skills_dir.exists():
        return findings

    skill_files = list(skills_dir.rglob("*.py")) + list(skills_dir.rglob("*.md"))

    for skill_file in skill_files:
        try:
            content = skill_file.read_text(errors="replace")
        except Exception as e:
            findings.append(Finding(
                severity="LOW",
                category="scan_error",
                target=str(skill_file),
                description=f"Could not read skill file: {e}",
                remediation="Check file permissions",
                control_id="P2.A-C01",
            ))
            continue

        for pattern, severity, category, description in SKILL_DANGEROUS_PATTERNS:
            if pattern.search(content):
                findings.append(Finding(
                    severity=severity,
                    category=f"skill_{category.replace(' ', '_')}",
                    target=str(skill_file),
                    description=description,
                    remediation=(
                        "Review skill source code. If legitimate, add to approved registry "
                        "with security review sign-off. If malicious, quarantine immediately: "
                        f"mv {skill_file} /tmp/quarantine/"
                    ),
                    control_id="P2.A-C01",
                ))

        # Check for Python AST validity (malformed skills may be obfuscated)
        if skill_file.suffix == ".py":
            try:
                ast.parse(content)
            except SyntaxError as e:
                findings.append(Finding(
                    severity="HIGH",
                    category="skill_syntax_error",
                    target=str(skill_file),
                    description=f"Skill has syntax errors — may be obfuscated: {e}",
                    remediation="Quarantine and manually inspect",
                    control_id="P2.A-C01",
                ))

        # Check for provenance manifest
        manifest = skill_file.parent / f"{skill_file.stem}.manifest.yaml"
        if not manifest.exists():
            findings.append(Finding(
                severity="MEDIUM",
                category="skill_no_manifest",
                target=str(skill_file),
                description="Skill has no provenance manifest — source and review status unknown",
                remediation=(
                    "Generate manifest: cp skills-registry/skill_manifest_template.yaml "
                    f"{manifest} && complete all fields"
                ),
                control_id="P2.A-C01",
            ))

    return findings


def scan_memory_sqlite(hermes_dir: Path) -> list[Finding]:
    """Scan SQLite memory databases for injection artifacts and credential patterns."""
    findings = []
    db_files = list(hermes_dir.rglob("*.db")) + list(hermes_dir.rglob("*.sqlite"))

    for db_path in db_files:
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Try common Hermes memory table names
            for table_query in [
                "SELECT name FROM sqlite_master WHERE type='table'",
            ]:
                try:
                    cursor.execute(table_query)
                    tables = [row[0] for row in cursor.fetchall()]
                    break
                except Exception:
                    tables = []

            for table in tables:
                try:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 1000")
                    rows = cursor.fetchall()
                    for row_idx, row in enumerate(rows):
                        row_text = " ".join(str(cell) for cell in row if cell)
                        for pattern, severity, category in MEMORY_INJECTION_PATTERNS:
                            if pattern.search(row_text):
                                findings.append(Finding(
                                    severity=severity,
                                    category=f"memory_{category}",
                                    target=f"{db_path}:{table}:row{row_idx}",
                                    description=f"Memory injection artifact detected: {category}",
                                    remediation=(
                                        f"Quarantine affected rows: DELETE FROM {table} WHERE rowid={row_idx+1}; "
                                        "Identify the external session that wrote this content."
                                    ),
                                    control_id="P4.M-C02",
                                ))
                except Exception:
                    pass
            conn.close()
        except Exception as e:
            findings.append(Finding(
                severity="LOW",
                category="scan_error",
                target=str(db_path),
                description=f"Could not scan memory database: {e}",
                remediation="Check database file integrity",
                control_id="P4.M-C02",
            ))

    return findings


def scan_memory_files(memories_dir: Path) -> list[Finding]:
    """Scan markdown memory files for injection artifacts."""
    findings = []
    if not memories_dir.exists():
        return findings

    for mem_file in memories_dir.rglob("*.md"):
        try:
            content = mem_file.read_text(errors="replace")
        except Exception:
            continue

        for pattern, severity, category in MEMORY_INJECTION_PATTERNS:
            if pattern.search(content):
                findings.append(Finding(
                    severity=severity,
                    category=f"memory_file_{category}",
                    target=str(mem_file),
                    description=f"Memory file contains injection artifact: {category}",
                    remediation=f"Review and quarantine: mv {mem_file} /tmp/quarantine/",
                    control_id="P4.M-C02",
                ))

    return findings


def scan_dependencies(project_dir: Path) -> list[Finding]:
    """Check for unpinned git dependencies in pyproject.toml, requirements.txt, uv.lock."""
    findings = []
    dep_files = ["pyproject.toml", "requirements.txt", "uv.lock", "requirements-dev.txt"]

    for dep_file_name in dep_files:
        dep_file = project_dir / dep_file_name
        if not dep_file.exists():
            continue

        content = dep_file.read_text(errors="replace")
        lines = content.split("\n")

        for i, line in enumerate(lines):
            # Look for git dependencies without commit pins
            if re.search(r"git\+https?://|git://", line):
                if not PINNED_DEP_PATTERN.search(line):
                    findings.append(Finding(
                        severity="HIGH",
                        category="dependency_unpinned_git",
                        target=f"{dep_file}:line{i+1}",
                        description=f"Git dependency without commit SHA pin: {line.strip()}",
                        remediation=(
                            "Pin to specific commit SHA: "
                            "git+https://github.com/org/repo@<40-char-sha>#egg=package"
                        ),
                        control_id="P2.A-C02",
                    ))

    return findings


def scan_env_permissions(hermes_dir: Path) -> list[Finding]:
    """Check .env file permission hardening."""
    findings = []
    env_paths = list(hermes_dir.rglob(".env")) + [Path.home() / ".hermes" / ".env"]

    for env_path in env_paths:
        if not env_path.exists():
            continue
        mode = oct(env_path.stat().st_mode)[-4:]
        if mode not in ("0600", "0400"):
            findings.append(Finding(
                severity="HIGH",
                category="env_permissions",
                target=str(env_path),
                description=f".env file has insecure permissions: {mode} (should be 0600)",
                remediation=f"chmod 0600 {env_path}",
                control_id="P1.S-C04",
            ))

        # Scan .env content for credential exposure
        try:
            env_content = env_path.read_text(errors="replace")
            for name, pattern in [
                ("anthropic_key", re.compile(r"sk-ant-[a-zA-Z0-9\-_]{20,}")),
                ("openai_key", re.compile(r"sk-(?:proj-)?[a-zA-Z0-9]{32,}")),
                ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}")),
            ]:
                if pattern.search(env_content):
                    findings.append(Finding(
                        severity="INFO",
                        category="env_contains_credentials",
                        target=str(env_path),
                        description=f".env contains {name} — migrate to HashiCorp Vault",
                        remediation=(
                            "Replace flat .env credentials with Vault dynamic secrets. "
                            "See supervisor/README.md for Vault setup."
                        ),
                        control_id="P1.S-C04",
                    ))
                    break  # One info finding per file
        except Exception:
            pass

    return findings


# ─── Main ─────────────────────────────────────────────────────────────────────

def run_scan(
    hermes_dir: Path,
    skills: bool = True,
    memory: bool = True,
    deps: bool = True,
    strict: bool = False,
) -> ScanResult:
    start = time.time()
    result = ScanResult()

    skills_dir = hermes_dir / "skills"
    memories_dir = hermes_dir / "memories"

    if skills:
        result.findings.extend(scan_skills(skills_dir))
        result.targets_scanned += len(list(skills_dir.rglob("*"))) if skills_dir.exists() else 0

    if memory:
        result.findings.extend(scan_memory_sqlite(hermes_dir))
        result.findings.extend(scan_memory_files(memories_dir))
        result.targets_scanned += len(list(memories_dir.rglob("*.md"))) if memories_dir.exists() else 0

    if deps:
        result.findings.extend(scan_dependencies(hermes_dir.parent))
        result.findings.extend(scan_env_permissions(hermes_dir))
        result.targets_scanned += 1

    result.scan_duration_ms = int((time.time() - start) * 1000)
    return result


def main():
    parser = argparse.ArgumentParser(description="AI SAFE² Scanner — Hermes Sovereign Runtime")
    parser.add_argument("--skills", action="store_true", help="Scan skills only")
    parser.add_argument("--memory", action="store_true", help="Scan memory only")
    parser.add_argument("--deps", action="store_true", help="Scan dependencies only")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on any HIGH or above")
    parser.add_argument("--watch", action="store_true", help="Run continuously (hourly)")
    parser.add_argument("--target", type=str, default="~/.hermes", help="Hermes home directory")
    parser.add_argument("--output", type=str, help="Write JSON report to file")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    args = parser.parse_args()

    hermes_dir = Path(args.target).expanduser()

    run_all = not (args.skills or args.memory or args.deps)

    def execute_scan():
        result = run_scan(
            hermes_dir,
            skills=run_all or args.skills,
            memory=run_all or args.memory,
            deps=run_all or args.deps,
            strict=args.strict,
        )

        if args.output:
            Path(args.output).write_text(json.dumps(result.to_dict(), indent=2))

        if not args.quiet:
            print(f"\n{'═'*60}")
            print(f"  AI SAFE² Scanner — Hermes Sovereign Runtime")
            print(f"  {result.scanned_at}")
            print(f"{'═'*60}")
            print(f"  Targets scanned : {result.targets_scanned}")
            print(f"  Total findings  : {len(result.findings)}")
            print(f"  Critical        : {result.critical_count}")
            print(f"  High            : {result.high_count}")
            print(f"  Status          : {'✅ PASS' if result.passed else '❌ FAIL — Critical findings present'}")
            print(f"{'═'*60}\n")

            for f in sorted(result.findings, key=lambda x: ["CRITICAL","HIGH","MEDIUM","LOW","INFO"].index(x.severity)):
                color = {"CRITICAL": "\033[91m", "HIGH": "\033[93m", "MEDIUM": "\033[94m",
                         "LOW": "\033[37m", "INFO": "\033[37m"}.get(f.severity, "")
                reset = "\033[0m"
                print(f"{color}[{f.severity:8}]{reset} [{f.control_id}] {f.category}")
                print(f"           Target: {f.target}")
                print(f"           {f.description}")
                print(f"           Fix: {f.remediation}\n")

        return result

    if args.watch:
        print("AI SAFE² Scanner — Watch mode (hourly). Ctrl+C to stop.\n")
        while True:
            result = execute_scan()
            if args.strict and (result.critical_count > 0 or result.high_count > 0):
                sys.exit(1)
            time.sleep(3600)
    else:
        result = execute_scan()
        if result.critical_count > 0:
            sys.exit(2)
        if args.strict and result.high_count > 0:
            sys.exit(1)
        sys.exit(0)


if __name__ == "__main__":
    main()
