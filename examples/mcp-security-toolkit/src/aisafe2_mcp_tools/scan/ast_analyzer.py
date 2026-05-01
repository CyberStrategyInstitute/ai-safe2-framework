"""
AI SAFE2 MCP Security Toolkit — mcp-scan: AST Analyzer
AST-based analysis catches vulnerabilities that regex cannot reliably detect —
specifically, data-flow paths where user-controlled input reaches dangerous sinks.

Primary target: RCE-001 — StdioServerParameters(command=<dynamic>)
This is the exact root cause of the OX Security April 2026 disclosure.
CVE-2026-30623 (LiteLLM), CVE-2026-30615 (Windsurf).

Why AST not regex for this:
  Regex on 'StdioServerParameters' would flag legitimate constant uses.
  AST analysis detects the specific pattern of a non-constant passed as 'command',
  which is the actual dangerous condition.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator

from aisafe2_mcp_tools.scan.findings import Finding


class ASTAnalyzer:
    """
    AST-based vulnerability scanner for MCP server source code.
    Catches data-flow patterns that regex analysis cannot reliably detect.
    """

    def analyze(self, source: str, filepath: str) -> Iterator[Finding]:
        """Parse source and yield any AST-detected findings."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            yield from self._check_stdio_server_parameters(node, filepath)

    def _check_stdio_server_parameters(
        self, node: ast.AST, filepath: str
    ) -> Iterator[Finding]:
        """
        Detect StdioServerParameters(command=<non-constant>).

        This is the architectural root cause of the OX Security April 2026
        supply chain event. The 'command' parameter MUST be a string constant.
        Any variable, expression, or external input reaching this parameter
        enables arbitrary OS command execution.

        Safe pattern:    StdioServerParameters(command="python", args=["-m", "server"])
        Unsafe pattern:  StdioServerParameters(command=user_input, args=[...])
        Unsafe pattern:  StdioServerParameters(command=f"{base_cmd} {extra}", args=[...])
        Unsafe pattern:  StdioServerParameters(command=config.get("cmd"), args=[...])
        """
        if not isinstance(node, ast.Call):
            return

        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name not in ("StdioServerParameters", "server_params", "stdio_server"):
            return

        for kw in node.keywords:
            if kw.arg != "command":
                continue
            # Check if the value is a constant (safe) or any other expression (unsafe)
            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                # Constant string — safe
                continue
            # Anything else: variable, f-string, attribute access, function call
            yield Finding(
                finding_id="RCE-001",
                severity="critical",
                cp5_control="MCP-1",
                title="Dynamic command construction in StdioServerParameters",
                description=(
                    "A non-constant value is passed as 'command' to StdioServerParameters. "
                    "This is the exact root cause of the OX Security April 2026 disclosure. "
                    "Any user, AI-generated, or external input that reaches this parameter "
                    "enables arbitrary OS command execution at process privilege level. "
                    "Anthropic confirmed this behavior is by design — sanitization is "
                    "the developer's responsibility."
                ),
                file=filepath,
                line=node.lineno,
                code_snippet=f"StdioServerParameters(command=<dynamic expression at line {node.lineno}>)",
                remediation=(
                    "The 'command' parameter MUST be a string literal constant. "
                    "NEVER allow user input, AI output, config values, or any external data "
                    "to influence this value. Use: StdioServerParameters(command='python', args=[...]) "
                    "See fix template: fixes/RCE-001.template"
                ),
                cve_refs=["CVE-2026-30623", "CVE-2026-30615", "CVE-2026-39884"],
                auto_fixable=False,
                manual_required=True,
            )
