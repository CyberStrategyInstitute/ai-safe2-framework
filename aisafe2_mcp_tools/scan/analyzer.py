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
from pathlib import Path

from aisafe2_mcp_tools.scan.ast_analyzer import ASTAnalyzer
from aisafe2_mcp_tools.scan.dep_checker import DependencyChecker
from aisafe2_mcp_tools.scan.findings import SEVERITY_ORDER, Finding
from aisafe2_mcp_tools.scan.pattern_scanner import PatternScanner
from aisafe2_mcp_tools.scan.reporter import html_report, json_report, terminal_report

logger = logging.getLogger(__name__)


class MCPScanner:
    """
    Full static analysis of an MCP server directory.

    Usage:
        scanner = MCPScanner("/path/to/mcp/server")
        findings = scanner.scan()
        print(scanner.terminal_report(findings))
    """

    def __init__(self, target_path: str) -> None:
        self.target = Path(target_path).resolve()
        self._ast = ASTAnalyzer()
        self._patterns = PatternScanner()
        self._deps = DependencyChecker()

    def scan(self) -> list[Finding]:
        """
        Run all analysis passes. Returns deduplicated, severity-sorted findings.
        """
        raw: list[Finding] = []

        # Source code analysis
        py_files = sorted(self.target.rglob("*.py"))
        for py_file in py_files:
            # Skip test files and __pycache__
            if "__pycache__" in str(py_file) or py_file.name.startswith("test_"):
                continue
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
        raw.extend(self._deps.check_directory(str(self.target)))

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
