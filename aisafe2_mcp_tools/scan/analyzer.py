"""
AI SAFE2 MCP Security Toolkit — mcp-scan: Main Analyzer
Coordinator that orchestrates AST analysis, pattern scanning,
and dependency checking into a unified scan result.

Each analysis concern lives in its own module:
  ast_analyzer.py      — AST-based data flow checks (RCE-001)
  pattern_scanner.py   — Regex pattern checks (RCE-002 through CONF-001)
  dep_checker.py       — Dependency CVE and version checks
  findings.py          — Finding data model
  reporter.py          — Output formatting

This file: scan orchestration, deduplication, sorting.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from aisafe2_mcp_tools.scan.ast_analyzer import ASTAnalyzer
from aisafe2_mcp_tools.scan.dep_checker import DependencyChecker
from aisafe2_mcp_tools.scan.findings import SEVERITY_ORDER, Finding
from aisafe2_mcp_tools.scan.pattern_scanner import PatternScanner
from aisafe2_mcp_tools.scan.reporter import html_report, json_report, terminal_report

logger = logging.getLogger(__name__)
EXCLUDED_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "build", "dist", "__pycache__"}


class ScanLimitExceeded(RuntimeError):
    """The requested scan cannot establish complete bounded coverage."""


class MCPScanner:
    """
    Full static analysis of an MCP server directory.

    Usage:
        scanner = MCPScanner("/path/to/mcp/server")
        findings = scanner.scan()
        print(scanner.terminal_report(findings))
    """

    def __init__(self, target_path: str, *, max_files: int = 10_000,
                 max_file_bytes: int = 5_000_000, max_total_bytes: int = 100_000_000) -> None:
        self.target = Path(target_path).resolve()
        self.max_files = max_files
        self.max_file_bytes = max_file_bytes
        self.max_total_bytes = max_total_bytes
        self._ast = ASTAnalyzer()
        self._patterns = PatternScanner()
        self._deps = DependencyChecker()

    def scan(self) -> list[Finding]:
        """
        Run all analysis passes. Returns deduplicated, severity-sorted findings.
        """
        raw: list[Finding] = []

        # Source code analysis
        file_count = 0
        total_bytes = 0
        for current, dirs, files in os.walk(self.target):
            dirs[:] = sorted(
                name for name in dirs
                if name not in EXCLUDED_DIRS and not name.startswith((".test-temp", "pytest-"))
            )
            for name in sorted(files):
                if not name.endswith(".py") or name.startswith("test_"):
                    continue
                py_file = Path(current) / name
                file_count += 1
                if file_count > self.max_files:
                    raise ScanLimitExceeded("MCP scan exceeded the file-count limit; coverage is incomplete")
                try:
                    size = py_file.stat().st_size
                except OSError as exc:
                    logger.warning("Skipping unreadable source file %s: %s", py_file, exc)
                    continue
                if size > self.max_file_bytes:
                    raise ScanLimitExceeded(f"MCP scan file exceeds the per-file byte limit: {py_file}")
                total_bytes += size
                if total_bytes > self.max_total_bytes:
                    raise ScanLimitExceeded("MCP scan exceeded the total-byte limit; coverage is incomplete")
            # Skip test files and __pycache__
                try:
                    source = py_file.read_text(encoding="utf-8", errors="replace")
                    lines = source.splitlines()
                    rel = str(py_file.relative_to(self.target))
                except OSError as exc:
                    logger.warning("Skipping unreadable source file %s: %s", py_file, exc)
                    continue

            # AST analysis (data-flow checks)
                raw.extend(self._ast.analyze(source, rel))

            # Pattern analysis (regex checks)
                raw.extend(self._patterns.scan_file(source, rel, lines))

        # Dependency analysis
        raw.extend(self._deps.check_directory(
            str(self.target), max_files=self.max_files,
            max_file_bytes=self.max_file_bytes, max_total_bytes=self.max_total_bytes,
        ))

        return self._deduplicate_and_sort(raw)

    @staticmethod
    def _deduplicate_and_sort(findings: list[Finding]) -> list[Finding]:
        """
        Deduplicate by (finding_id, file, line) and sort by severity (critical first),
        then by file, then by line number.
        """
        seen: set[tuple[str, str, int]] = set()
        unique: list[Finding] = []
        for f in findings:
            key = (f.finding_id, f.file, f.line)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return sorted(
            unique,
            key=lambda f: (-SEVERITY_ORDER.get(f.severity, 0), f.file, f.line),
        )

    def terminal_report(self, findings: list[Finding]) -> str:
        return terminal_report(findings, str(self.target))

    def json_report(self, findings: list[Finding]) -> str:
        return json_report(findings, str(self.target))

    def html_report(self, findings: list[Finding]) -> str:
        return html_report(findings, str(self.target))
