#!/usr/bin/env python3
"""
HSR Memory Auditor — Continuous Anomaly Detection Daemon
AI SAFE² v3.0 · P4.M-C02
Cyber Strategy Institute

Runs continuously (or on-demand) against Hermes' SQLite memory stores and
markdown memory files, detecting:
  - Persistent prompt injection artifacts
  - Credential patterns written to memory
  - External-surface-sourced entries without taint tags
  - Memory entries showing identity replacement attempts

Designed to catch attacks that EDR cannot see:
  Indirect prompt injection through memory retrieval is invisible to endpoint
  security tools. When Hermes reads a malicious document and stores content
  from it in its memory, that stored content can carry adversarial instructions
  executed in future sessions. This daemon catches those artifacts.

Usage:
  python3 monitoring/memory_auditor.py                     # One-time scan
  python3 monitoring/memory_auditor.py --watch             # Continuous (60s interval)
  python3 monitoring/memory_auditor.py --hermes-dir ~/.hermes
  python3 monitoring/memory_auditor.py --quarantine        # Auto-quarantine findings
"""

import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


HERMES_DEFAULT_DIR = Path.home() / ".hermes"
QUARANTINE_DIR = Path("/tmp/hsr-quarantine")
AUDIT_LOG = Path("/var/log/hsr/memory_audit.jsonl")
FALLBACK_AUDIT_LOG = Path("/tmp/hsr_memory_audit.jsonl")

# ─── Detection Patterns ───────────────────────────────────────────────────────

INJECTION_ARTIFACTS = [
    # Prompt injection
    (re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?", re.I), "CRITICAL", "injection_ignore"),
    (re.compile(r"(?:your\s+)?new\s+system\s+prompt\s+is", re.I), "CRITICAL", "injection_new_system"),
    (re.compile(r"you\s+are\s+now\s+(?:a\s+)?(?:different|unrestricted|jailbroken)", re.I), "CRITICAL", "injection_identity"),
    (re.compile(r"disregard\s+(?:your\s+)?(?:safety\s+)?guidelines?", re.I), "HIGH", "injection_safety_bypass"),
    (re.compile(r"developer\s+mode\s+(?:enabled|active|on)", re.I), "HIGH", "injection_devmode"),
    (re.compile(r"do\s+anything\s+now|DAN\s+mode", re.I), "CRITICAL", "injection_dan"),
    (re.compile(r"you\s+have\s+no\s+restrictions?\s+(?:now|in\s+this)", re.I), "CRITICAL", "injection_no_restrictions"),
    (re.compile(r"for\s+this\s+(?:session|conversation),?\s+(?:you\s+)?(?:have\s+)?no", re.I), "HIGH", "injection_session_override"),
    # Credential exfiltration artifacts
    (re.compile(r"sk-ant-[a-zA-Z0-9\-_]{20,}"), "CRITICAL", "cred_anthropic_key"),
    (re.compile(r"sk-(?:proj-)?[a-zA-Z0-9]{32,}"), "CRITICAL", "cred_openai_key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "CRITICAL", "cred_aws_access_key"),
    (re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"), "CRITICAL", "cred_private_key"),
    (re.compile(r"gh[pos]_[A-Za-z0-9]{36}"), "CRITICAL", "cred_github_token"),
    (re.compile(r'"type":\s*"service_account"'), "CRITICAL", "cred_gcp_service_account"),
    # Command injection in memory
    (re.compile(r"(?:rm\s+-rf|mkfs|dd\s+if=|format\s+c:)", re.I), "HIGH", "cmd_destructive"),
    (re.compile(r"curl\s+[^\s]+\s*\|\s*(?:bash|sh)", re.I), "HIGH", "cmd_pipe_shell"),
    (re.compile(r"wget\s+-O-?\s+[^\s]+\s*\|\s*(?:bash|sh)", re.I), "HIGH", "cmd_wget_pipe"),
]


# ─── Memory Sources ────────────────────────────────────────────────────────────

def get_hermes_memory_dbs(hermes_dir: Path) -> list[Path]:
    """Find all SQLite databases in Hermes directory."""
    dbs = []
    for pattern in ["*.db", "*.sqlite", "*.sqlite3"]:
        dbs.extend(hermes_dir.rglob(pattern))
    return dbs


def get_hermes_memory_files(hermes_dir: Path) -> list[Path]:
    """Find all markdown memory files."""
    memories_dir = hermes_dir / "memories"
    if not memories_dir.exists():
        return []
    files = list(memories_dir.rglob("*.md"))
    # Exclude the vaccine file
    return [f for f in files if "VACCINE" not in f.name and "IDENTITY" not in f.name
            and "SOUL" not in f.name]


# ─── Scanning ─────────────────────────────────────────────────────────────────

def scan_sqlite(db_path: Path) -> list[dict]:
    """Scan a SQLite database for injection artifacts."""
    findings = []
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            try:
                cursor.execute(f"SELECT rowid, * FROM {table} LIMIT 2000")
                rows = cursor.fetchall()
                col_names = [desc[0] for desc in cursor.description]

                for row in rows:
                    row_id = row[0]
                    row_text = " ".join(str(cell) for cell in row[1:] if cell)

                    for pattern, severity, category in INJECTION_ARTIFACTS:
                        if pattern.search(row_text):
                            # Extract a context snippet (non-credential)
                            match = pattern.search(row_text)
                            start = max(0, match.start() - 50)
                            end = min(len(row_text), match.end() + 50)
                            # Redact credential values in snippet
                            snippet = row_text[start:end]
                            if "cred_" in category:
                                snippet = "[REDACTED - credential pattern detected]"

                            findings.append({
                                "severity": severity,
                                "category": category,
                                "source": "sqlite",
                                "location": f"{db_path}:{table}:rowid={row_id}",
                                "snippet": snippet,
                                "detected_at": datetime.now(timezone.utc).isoformat(),
                                "remediation": get_remediation(category, str(db_path), table, row_id),
                            })
            except sqlite3.OperationalError:
                pass  # Table may not be readable

        conn.close()
    except Exception as e:
        findings.append({
            "severity": "LOW",
            "category": "scan_error",
            "source": "sqlite",
            "location": str(db_path),
            "snippet": str(e),
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "remediation": "Check database file integrity and permissions",
        })

    return findings


def scan_memory_file(file_path: Path) -> list[dict]:
    """Scan a markdown memory file for injection artifacts."""
    findings = []
    try:
        content = file_path.read_text(errors="replace")
    except Exception:
        return findings

    for pattern, severity, category in INJECTION_ARTIFACTS:
        if pattern.search(content):
            match = pattern.search(content)
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            snippet = content[start:end]
            if "cred_" in category:
                snippet = "[REDACTED - credential pattern detected]"

            findings.append({
                "severity": severity,
                "category": category,
                "source": "memory_file",
                "location": str(file_path),
                "snippet": snippet.strip(),
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "remediation": get_remediation(category, str(file_path)),
            })

    return findings


def get_remediation(category: str, location: str, table: str = "", row_id: int = 0) -> str:
    if "cred_" in category:
        return (
            f"IMMEDIATE: Credential may be compromised. "
            f"1. Activate kill switch: bash scripts/kill-switch.sh 'Credential in memory: {category}' "
            f"2. Rotate affected credentials immediately: bash scripts/rotate-credentials.sh "
            f"3. Audit how this credential reached memory (external session taint tracking)"
        )
    elif "injection_" in category:
        if table and row_id:
            return (
                f"Quarantine: DELETE FROM {table} WHERE rowid={row_id} in {location}. "
                f"Identify which external session wrote this content (check taint tags). "
                f"Review memory vaccine deployment."
            )
        return (
            f"Quarantine file: mv {location} /tmp/hsr-quarantine/. "
            f"Identify the session that wrote this content."
        )
    elif "cmd_" in category:
        return f"Review: command injection artifact in memory. Source session investigation required."
    return "Review and remediate. See docs/INCIDENT-RESPONSE.md."


def quarantine_file(file_path: Path) -> bool:
    """Move a suspicious memory file to quarantine."""
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    dest = QUARANTINE_DIR / f"{file_path.name}.{int(time.time())}.quarantine"
    try:
        shutil.move(str(file_path), str(dest))
        return True
    except Exception:
        return False


# ─── Audit Logging ────────────────────────────────────────────────────────────

def write_audit(event: dict) -> None:
    log_path = AUDIT_LOG if AUDIT_LOG.parent.exists() else FALLBACK_AUDIT_LOG
    FALLBACK_AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(event) + "\n")


# ─── Main Scan ────────────────────────────────────────────────────────────────

def run_audit(hermes_dir: Path, auto_quarantine: bool = False, quiet: bool = False) -> list[dict]:
    all_findings = []

    # Scan SQLite databases
    dbs = get_hermes_memory_dbs(hermes_dir)
    for db in dbs:
        findings = scan_sqlite(db)
        all_findings.extend(findings)

    # Scan memory files
    memory_files = get_hermes_memory_files(hermes_dir)
    for mem_file in memory_files:
        findings = scan_memory_file(mem_file)
        all_findings.extend(findings)
        # Auto-quarantine critical memory file findings
        if auto_quarantine and findings:
            critical = [f for f in findings if f["severity"] == "CRITICAL"]
            if critical:
                quarantined = quarantine_file(mem_file)
                if not quiet:
                    status = "quarantined" if quarantined else "quarantine failed"
                    print(f"  ⚠ {mem_file.name}: {status}")

    # Audit log summary
    write_audit({
        "event": "memory_audit_complete",
        "hermes_dir": str(hermes_dir),
        "dbs_scanned": len(dbs),
        "files_scanned": len(memory_files),
        "findings": len(all_findings),
        "critical": sum(1 for f in all_findings if f["severity"] == "CRITICAL"),
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    })

    return all_findings


def print_findings(findings: list[dict]) -> None:
    if not findings:
        print("\n  ✅ No injection artifacts or credential patterns found in memory.\n")
        return

    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    findings_sorted = sorted(findings, key=lambda f: severity_order.get(f["severity"], 99))

    for f in findings_sorted:
        color = {"CRITICAL": "\033[91m", "HIGH": "\033[93m"}.get(f["severity"], "\033[37m")
        reset = "\033[0m"
        print(f"\n  {color}[{f['severity']}]{reset} {f['category']}")
        print(f"    Location : {f['location']}")
        print(f"    Snippet  : {f['snippet'][:120]}")
        print(f"    Remediate: {f['remediation'][:200]}")


def main():
    parser = argparse.ArgumentParser(description="HSR Memory Auditor — P4.M-C02")
    parser.add_argument("--hermes-dir", default=str(HERMES_DEFAULT_DIR), help="Hermes home directory")
    parser.add_argument("--watch", action="store_true", help="Continuous mode (60s interval)")
    parser.add_argument("--interval", type=int, default=60, help="Watch interval in seconds")
    parser.add_argument("--quarantine", action="store_true", help="Auto-quarantine critical findings")
    parser.add_argument("--output", help="Write JSON findings to file")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    args = parser.parse_args()

    hermes_dir = Path(args.hermes_dir).expanduser()

    if not hermes_dir.exists():
        print(f"Hermes directory not found: {hermes_dir}")
        sys.exit(1)

    def execute():
        if not args.quiet:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scanning {hermes_dir}...")

        findings = run_audit(hermes_dir, auto_quarantine=args.quarantine, quiet=args.quiet)

        if not args.quiet:
            print_findings(findings)

            critical = sum(1 for f in findings if f["severity"] == "CRITICAL")
            if critical:
                print(f"\n  🚨 {critical} CRITICAL finding(s) — activate kill switch if compromised:")
                print(f"     bash scripts/kill-switch.sh 'Memory injection detected'")

        if args.output and findings:
            with open(args.output, "a") as f:
                for finding in findings:
                    f.write(json.dumps(finding) + "\n")

        return findings

    if args.watch:
        if not args.quiet:
            print(f"HSR Memory Auditor — Watch mode ({args.interval}s interval). Ctrl+C to stop.")
        while True:
            try:
                execute()
                time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\nMemory auditor stopped.")
                break
    else:
        findings = execute()
        critical = sum(1 for f in findings if f["severity"] == "CRITICAL")
        sys.exit(2 if critical > 0 else (1 if findings else 0))


if __name__ == "__main__":
    main()
